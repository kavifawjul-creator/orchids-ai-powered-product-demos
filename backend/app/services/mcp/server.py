from mcp.server.fastmcp import FastMCP
from ..browser.service import browser_service
from ...models.schemas import BrowserAction
import logging

logger = logging.getLogger(__name__)

mcp = FastMCP("Browser Automation")

@mcp.tool()
async def navigate(session_id: str, url: str) -> str:
    """Navigate the browser to a specific URL."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    result = await session.navigate(url)
    return f"Navigated to {url}. Success: {result.get('success')}"

@mcp.tool()
async def click(session_id: str, selector: str) -> str:
    """Click an element on the page using a CSS selector."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    result = await session.click(selector)
    if result.get("success"):
        return f"Clicked element: {selector}"
    return f"Failed to click {selector}: {result.get('error')}"

@mcp.tool()
async def type_text(session_id: str, selector: str, text: str) -> str:
    """Type text into an input field."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    result = await session.type_text(selector, text)
    if result.get("success"):
        return f"Typed '{text}' into {selector}"
    return f"Failed to type into {selector}: {result.get('error')}"

@mcp.tool()
async def hover(session_id: str, selector: str) -> str:
    """Hover over an element."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    result = await session.hover(selector)
    if result.get("success"):
        return f"Hovered over {selector}"
    return f"Failed to hover over {selector}: {result.get('error')}"

@mcp.tool()
async def scroll(session_id: str, direction: str = "down", amount: int = 500) -> str:
    """Scroll the page."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    result = await session.scroll(direction, amount)
    return f"Scrolled {direction} by {amount}px."

@mcp.tool()
async def wait(session_id: str, ms: int = 1000) -> str:
    """Wait for a specific amount of time in milliseconds."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    await session.wait(ms)
    return f"Waited for {ms}ms."

@mcp.tool()
async def screenshot(session_id: str, name: str = "screenshot") -> str:
    """Take a screenshot of the current page."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    result = await session.screenshot(name)
    if result.get("success"):
        return f"Screenshot saved to {result.get('path')}"
    return f"Failed to take screenshot: {result.get('error')}"

@mcp.resource("browser://{session_id}/accessibility")
async def get_accessibility(session_id: str) -> str:
    """Get the accessibility tree of the current page."""
    session = await browser_service.get_session(session_id)
    if not session:
        return f"Error: Session {session_id} not found."
    
    tree = await session.get_accessibility_tree()
    import json
    return json.dumps(tree, indent=2)

@mcp.resource("browser://{session_id}/url")
async def get_url(session_id: str) -> str:
    """Get the current URL of the page."""
    session = await browser_service.get_session(session_id)
    if not session or not session.page:
        return "No active session or page."
    return session.page.url
