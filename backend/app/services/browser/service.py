import asyncio
import base64
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from ...models.schemas import BrowserAction, RecordingEvent
from ...core.events import event_bus, EventTypes
from ...core.config import settings

class BrowserSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.recording_events: List[RecordingEvent] = []
        self.start_time: Optional[float] = None
        self._frame_callback: Optional[Callable] = None
        self._playwright = None
    
    async def start(self, headless: bool = True) -> str:
        self._playwright = await async_playwright().start()
        
        self.browser = await self._playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,
            record_video_dir="/tmp/autovid/recordings" if not headless else None
        )
        
        self.page = await self.context.new_page()
        self.start_time = asyncio.get_event_loop().time()
        
        self.page.on("console", self._on_console)
        self.page.on("pageerror", self._on_error)
        
        return self.session_id
    
    async def stop(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        await self.page.goto(url, wait_until="networkidle")
        self._record_event("navigate", url=url)
        return {"success": True, "url": self.page.url}
    
    async def click(self, selector: str) -> Dict[str, Any]:
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.click()
                self._record_event("click", target=selector)
                return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "error": "Element not found"}
    
    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.fill(text)
                self._record_event("type", target=selector, value=text)
                return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "error": "Element not found"}
    
    async def hover(self, selector: str) -> Dict[str, Any]:
        try:
            element = await self.page.wait_for_selector(selector, timeout=5000)
            if element:
                await element.hover()
                self._record_event("hover", target=selector)
                return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "error": "Element not found"}
    
    async def scroll(self, direction: str = "down", amount: int = 500) -> Dict[str, Any]:
        delta = amount if direction == "down" else -amount
        await self.page.mouse.wheel(0, delta)
        self._record_event("scroll", value=f"{direction}:{amount}")
        return {"success": True, "direction": direction, "amount": amount}
    
    async def wait(self, ms: int) -> Dict[str, Any]:
        await asyncio.sleep(ms / 1000)
        self._record_event("wait", value=str(ms))
        return {"success": True, "waited_ms": ms}
    
    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> Dict[str, Any]:
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def screenshot(self, name: Optional[str] = None) -> Dict[str, Any]:
        path = f"/tmp/autovid/screenshots/{self.session_id}_{name or 'screenshot'}_{int(self._get_timestamp())}.png"
        await self.page.screenshot(path=path, full_page=False)
        self._record_event("screenshot", screenshot_path=path)
        return {"success": True, "path": path}
    
    async def get_screenshot_base64(self) -> str:
        screenshot = await self.page.screenshot(type="png")
        return base64.b64encode(screenshot).decode("utf-8")
    
    async def execute_action(self, action: BrowserAction) -> Dict[str, Any]:
        action_map = {
            "navigate": lambda: self.navigate(action.url or action.value),
            "click": lambda: self.click(action.selector),
            "type": lambda: self.type_text(action.selector, action.value),
            "hover": lambda: self.hover(action.selector),
            "scroll": lambda: self.scroll(action.value or "down", 500),
            "wait": lambda: self.wait(int(action.value) if action.value else 1000),
            "wait_for": lambda: self.wait_for_selector(action.selector),
            "screenshot": lambda: self.screenshot(action.value)
        }
        
        handler = action_map.get(action.action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action.action}"}
        
        result = await handler()
        
        if action.wait_ms > 0:
            await self.wait(action.wait_ms)
        
        return result
    
    async def get_page_content(self) -> str:
        return await self.page.content()
    
    async def get_accessibility_tree(self) -> Dict[str, Any]:
        return await self.page.accessibility.snapshot()
    
    async def evaluate(self, script: str) -> Any:
        return await self.page.evaluate(script)
    
    def get_recording_events(self) -> List[RecordingEvent]:
        return self.recording_events
    
    def set_frame_callback(self, callback: Callable):
        self._frame_callback = callback
    
    def _get_timestamp(self) -> float:
        if self.start_time is None:
            return 0
        return asyncio.get_event_loop().time() - self.start_time
    
    def _record_event(
        self,
        event_type: str,
        target: Optional[str] = None,
        value: Optional[str] = None,
        url: Optional[str] = None,
        screenshot_path: Optional[str] = None
    ):
        event = RecordingEvent(
            timestamp=self._get_timestamp(),
            event_type=event_type,
            action=event_type,
            target=target,
            screenshot_path=screenshot_path,
            metadata={"value": value, "url": url}
        )
        self.recording_events.append(event)
    
    def _on_console(self, msg):
        pass
    
    def _on_error(self, error):
        self._record_event("error", value=str(error))


class BrowserService:
    def __init__(self):
        self._sessions: Dict[str, BrowserSession] = {}
    
    async def create_session(self, session_id: str, headless: bool = True) -> BrowserSession:
        session = BrowserSession(session_id)
        await session.start(headless=headless)
        self._sessions[session_id] = session
        return session
    
    async def get_session(self, session_id: str) -> Optional[BrowserSession]:
        return self._sessions.get(session_id)
    
    async def destroy_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            await session.stop()
            del self._sessions[session_id]
            return True
        return False
    
    async def execute_action(self, session_id: str, action: BrowserAction) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        return await session.execute_action(action)
    
    async def get_screenshot(self, session_id: str) -> Optional[str]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        return await session.get_screenshot_base64()

browser_service = BrowserService()
