import asyncio
import base64
import logging
import time
from typing import Optional, Dict, Any, List, Callable

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

from app.core.config import settings
from app.models.browser import (
    BrowserAction,
    BrowserActionType,
    BrowserActionResult,
    BrowserSessionConfig,
    BrowserSessionInfo,
    ElementInfo,
    PageInfo,
    MCPToolDefinition,
    MCPToolCall,
    MCPToolResult,
)

logger = logging.getLogger(__name__)


MCP_BROWSER_TOOLS: List[MCPToolDefinition] = [
    MCPToolDefinition(
        name="browser_navigate",
        description="Navigate to a URL in the browser",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to navigate to"},
                "wait_until": {
                    "type": "string",
                    "enum": ["load", "domcontentloaded", "networkidle"],
                    "default": "load",
                },
            },
            "required": ["url"],
        },
    ),
    MCPToolDefinition(
        name="browser_click",
        description="Click on an element using CSS selector or text",
        input_schema={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector or text to find element"},
                "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                "click_count": {"type": "integer", "default": 1},
            },
            "required": ["selector"],
        },
    ),
    MCPToolDefinition(
        name="browser_type",
        description="Type text into an input field",
        input_schema={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector for the input element"},
                "text": {"type": "string", "description": "Text to type"},
                "delay": {"type": "integer", "description": "Delay between keystrokes in ms", "default": 0},
                "clear": {"type": "boolean", "description": "Clear existing text first", "default": True},
            },
            "required": ["selector", "text"],
        },
    ),
    MCPToolDefinition(
        name="browser_screenshot",
        description="Take a screenshot of the current page",
        input_schema={
            "type": "object",
            "properties": {
                "full_page": {"type": "boolean", "default": False},
                "selector": {"type": "string", "description": "Optional selector to screenshot specific element"},
            },
        },
    ),
    MCPToolDefinition(
        name="browser_scroll",
        description="Scroll the page",
        input_schema={
            "type": "object",
            "properties": {
                "direction": {"type": "string", "enum": ["up", "down", "left", "right"]},
                "amount": {"type": "integer", "description": "Pixels to scroll", "default": 500},
                "selector": {"type": "string", "description": "Optional element to scroll within"},
            },
            "required": ["direction"],
        },
    ),
    MCPToolDefinition(
        name="browser_wait",
        description="Wait for a condition",
        input_schema={
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["time", "selector", "navigation"],
                    "description": "Type of wait",
                },
                "value": {"type": "string", "description": "Selector or time in ms"},
                "timeout": {"type": "integer", "default": 30000},
            },
            "required": ["type"],
        },
    ),
    MCPToolDefinition(
        name="browser_hover",
        description="Hover over an element",
        input_schema={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector for element to hover"},
            },
            "required": ["selector"],
        },
    ),
    MCPToolDefinition(
        name="browser_select",
        description="Select an option from a dropdown",
        input_schema={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector for select element"},
                "value": {"type": "string", "description": "Value to select"},
            },
            "required": ["selector", "value"],
        },
    ),
    MCPToolDefinition(
        name="browser_press_key",
        description="Press a keyboard key",
        input_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Key to press (e.g., Enter, Tab, Escape)"},
                "modifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Modifier keys (Control, Shift, Alt, Meta)",
                },
            },
            "required": ["key"],
        },
    ),
    MCPToolDefinition(
        name="browser_get_page_info",
        description="Get information about the current page",
        input_schema={"type": "object", "properties": {}},
    ),
    MCPToolDefinition(
        name="browser_get_elements",
        description="Get information about elements matching a selector",
        input_schema={
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["selector"],
        },
    ),
]


class MCPBrowserService:
    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._event_callbacks: List[Callable] = []

    def register_event_callback(self, callback: Callable):
        self._event_callbacks.append(callback)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    async def initialize(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ]
            )
            logger.info("Playwright browser initialized")

    async def shutdown(self):
        for session_id in list(self._sessions.keys()):
            await self.close_session(session_id)
        
        if self._browser:
            await self._browser.close()
            self._browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.info("Playwright browser shut down")

    async def create_session(
        self,
        project_id: str,
        config: Optional[BrowserSessionConfig] = None,
        sandbox_id: Optional[str] = None,
    ) -> BrowserSessionInfo:
        await self.initialize()
        
        config = config or BrowserSessionConfig()
        session_info = BrowserSessionInfo(
            project_id=project_id,
            sandbox_id=sandbox_id,
            config=config,
        )

        context_options = {
            "viewport": {"width": config.viewport_width, "height": config.viewport_height},
            "device_scale_factor": config.device_scale_factor,
            "locale": config.locale,
            "timezone_id": config.timezone,
            "color_scheme": config.color_scheme,
        }

        if config.user_agent:
            context_options["user_agent"] = config.user_agent

        if config.record_video and config.video_dir:
            context_options["record_video_dir"] = config.video_dir
            context_options["record_video_size"] = {
                "width": config.viewport_width,
                "height": config.viewport_height,
            }

        context = await self._browser.new_context(**context_options)
        page = await context.new_page()

        self._sessions[session_info.id] = {
            "info": session_info,
            "context": context,
            "page": page,
            "actions": [],
        }

        session_info.status = "ready"
        await self._emit_event("BROWSER_SESSION_CREATED", {"session_id": session_info.id})
        
        return session_info

    async def get_session(self, session_id: str) -> Optional[BrowserSessionInfo]:
        session = self._sessions.get(session_id)
        return session["info"] if session else None

    async def get_page(self, session_id: str) -> Optional[Page]:
        session = self._sessions.get(session_id)
        return session["page"] if session else None

    async def close_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False

        try:
            context: BrowserContext = session["context"]
            await context.close()
            del self._sessions[session_id]
            await self._emit_event("BROWSER_SESSION_CLOSED", {"session_id": session_id})
            return True
        except Exception as e:
            logger.error(f"Failed to close session {session_id}: {e}")
            return False

    async def execute_action(self, session_id: str, action: BrowserAction) -> BrowserActionResult:
        session = self._sessions.get(session_id)
        if not session:
            return BrowserActionResult(
                action_id=action.id,
                success=False,
                error="Session not found",
            )

        page: Page = session["page"]
        info: BrowserSessionInfo = session["info"]
        start_time = time.time()

        try:
            result = await self._execute_action_impl(page, action)
            duration_ms = int((time.time() - start_time) * 1000)

            info.current_url = page.url
            info.current_title = await page.title()
            info.last_action_at = action.timestamp
            info.action_count += 1

            session["actions"].append(action)

            action_result = BrowserActionResult(
                action_id=action.id,
                success=True,
                result=result,
                duration_ms=duration_ms,
                page_url=info.current_url,
                page_title=info.current_title,
            )

            await self._emit_event("BROWSER_ACTION_COMPLETED", {
                "session_id": session_id,
                "action_id": action.id,
                "action_type": action.action_type.value,
                "duration_ms": duration_ms,
            })

            return action_result

        except Exception as e:
            logger.error(f"Action failed: {e}")
            duration_ms = int((time.time() - start_time) * 1000)
            
            return BrowserActionResult(
                action_id=action.id,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
                page_url=page.url,
            )

    async def _execute_action_impl(self, page: Page, action: BrowserAction) -> Any:
        if action.action_type == BrowserActionType.NAVIGATE:
            wait_until = action.options.get("wait_until", "load")
            response = await page.goto(action.url, wait_until=wait_until, timeout=action.timeout)
            return {"status": response.status if response else None, "url": page.url}

        elif action.action_type == BrowserActionType.CLICK:
            button = action.options.get("button", "left")
            click_count = action.options.get("click_count", 1)
            await page.click(action.selector, button=button, click_count=click_count, timeout=action.timeout)
            return {"clicked": action.selector}

        elif action.action_type == BrowserActionType.TYPE:
            if action.options.get("clear", True):
                await page.fill(action.selector, "", timeout=action.timeout)
            delay = action.options.get("delay", 0)
            await page.type(action.selector, action.value, delay=delay, timeout=action.timeout)
            return {"typed": action.value, "into": action.selector}

        elif action.action_type == BrowserActionType.SCREENSHOT:
            full_page = action.options.get("full_page", False)
            if action.selector:
                element = page.locator(action.selector)
                screenshot_bytes = await element.screenshot(timeout=action.timeout)
            else:
                screenshot_bytes = await page.screenshot(full_page=full_page, timeout=action.timeout)
            return {"screenshot_base64": base64.b64encode(screenshot_bytes).decode()}

        elif action.action_type == BrowserActionType.SCROLL:
            direction = action.options.get("direction", "down")
            amount = action.options.get("amount", 500)
            
            scroll_x, scroll_y = 0, 0
            if direction == "down":
                scroll_y = amount
            elif direction == "up":
                scroll_y = -amount
            elif direction == "right":
                scroll_x = amount
            elif direction == "left":
                scroll_x = -amount

            if action.selector:
                await page.locator(action.selector).evaluate(
                    f"el => el.scrollBy({scroll_x}, {scroll_y})"
                )
            else:
                await page.evaluate(f"window.scrollBy({scroll_x}, {scroll_y})")
            return {"scrolled": direction, "amount": amount}

        elif action.action_type == BrowserActionType.WAIT:
            wait_type = action.options.get("type", "time")
            if wait_type == "time":
                ms = int(action.value) if action.value else 1000
                await asyncio.sleep(ms / 1000)
            elif wait_type == "selector":
                await page.wait_for_selector(action.selector, timeout=action.timeout)
            elif wait_type == "navigation":
                await page.wait_for_load_state("networkidle", timeout=action.timeout)
            return {"waited": wait_type}

        elif action.action_type == BrowserActionType.HOVER:
            await page.hover(action.selector, timeout=action.timeout)
            return {"hovered": action.selector}

        elif action.action_type == BrowserActionType.SELECT:
            await page.select_option(action.selector, action.value, timeout=action.timeout)
            return {"selected": action.value, "in": action.selector}

        elif action.action_type == BrowserActionType.PRESS_KEY:
            modifiers = action.options.get("modifiers", [])
            key = action.value
            if modifiers:
                key = "+".join(modifiers + [key])
            await page.keyboard.press(key)
            return {"pressed": key}

        elif action.action_type == BrowserActionType.WAIT_FOR_SELECTOR:
            await page.wait_for_selector(action.selector, timeout=action.timeout)
            return {"found": action.selector}

        elif action.action_type == BrowserActionType.WAIT_FOR_NAVIGATION:
            await page.wait_for_load_state("networkidle", timeout=action.timeout)
            return {"navigated": True}

        elif action.action_type == BrowserActionType.EVALUATE:
            result = await page.evaluate(action.value)
            return {"result": result}

        return None

    async def execute_mcp_tool(self, session_id: str, tool_call: MCPToolCall) -> MCPToolResult:
        action = self._mcp_tool_to_action(tool_call)
        if not action:
            return MCPToolResult(
                tool_name=tool_call.tool_name,
                success=False,
                result=None,
                error=f"Unknown tool: {tool_call.tool_name}",
            )

        result = await self.execute_action(session_id, action)
        return MCPToolResult(
            tool_name=tool_call.tool_name,
            success=result.success,
            result=result.result,
            error=result.error,
        )

    def _mcp_tool_to_action(self, tool_call: MCPToolCall) -> Optional[BrowserAction]:
        args = tool_call.arguments
        
        mapping = {
            "browser_navigate": (BrowserActionType.NAVIGATE, {"url": args.get("url")}),
            "browser_click": (BrowserActionType.CLICK, {"selector": args.get("selector")}),
            "browser_type": (BrowserActionType.TYPE, {"selector": args.get("selector"), "value": args.get("text")}),
            "browser_screenshot": (BrowserActionType.SCREENSHOT, {}),
            "browser_scroll": (BrowserActionType.SCROLL, {}),
            "browser_wait": (BrowserActionType.WAIT, {}),
            "browser_hover": (BrowserActionType.HOVER, {"selector": args.get("selector")}),
            "browser_select": (BrowserActionType.SELECT, {"selector": args.get("selector"), "value": args.get("value")}),
            "browser_press_key": (BrowserActionType.PRESS_KEY, {"value": args.get("key")}),
        }

        if tool_call.tool_name not in mapping:
            return None

        action_type, base_params = mapping[tool_call.tool_name]
        options = {k: v for k, v in args.items() if k not in ["url", "selector", "text", "value", "key"]}

        return BrowserAction(
            action_type=action_type,
            url=base_params.get("url"),
            selector=base_params.get("selector"),
            value=base_params.get("value"),
            options=options,
        )

    async def take_screenshot(self, session_id: str, full_page: bool = False) -> Optional[bytes]:
        page = await self.get_page(session_id)
        if not page:
            return None
        return await page.screenshot(full_page=full_page)

    async def get_page_info(self, session_id: str) -> Optional[PageInfo]:
        page = await self.get_page(session_id)
        if not page:
            return None

        viewport = page.viewport_size or {"width": 1920, "height": 1080}
        scroll_pos = await page.evaluate("() => ({x: window.scrollX, y: window.scrollY})")
        content_size = await page.evaluate(
            "() => ({width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight})"
        )

        return PageInfo(
            url=page.url,
            title=await page.title(),
            viewport=viewport,
            scroll_position=scroll_pos,
            content_size=content_size,
        )

    async def get_elements(self, session_id: str, selector: str, limit: int = 10) -> List[ElementInfo]:
        page = await self.get_page(session_id)
        if not page:
            return []

        elements = []
        locators = page.locator(selector)
        count = await locators.count()

        for i in range(min(count, limit)):
            el = locators.nth(i)
            try:
                tag = await el.evaluate("el => el.tagName.toLowerCase()")
                text = await el.inner_text() if await el.is_visible() else None
                box = await el.bounding_box()
                
                elements.append(ElementInfo(
                    tag_name=tag,
                    text=text[:100] if text else None,
                    bounding_box=box,
                    is_visible=await el.is_visible(),
                    is_enabled=await el.is_enabled(),
                ))
            except Exception:
                continue

        return elements

    def get_available_tools(self) -> List[MCPToolDefinition]:
        return MCP_BROWSER_TOOLS


browser_service = MCPBrowserService()
