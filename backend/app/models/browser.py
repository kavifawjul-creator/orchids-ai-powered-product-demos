from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal
from enum import Enum
from datetime import datetime
import uuid


class BrowserActionType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    HOVER = "hover"
    SELECT = "select"
    PRESS_KEY = "press_key"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"
    EVALUATE = "evaluate"


class BrowserAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: BrowserActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    timeout: int = 30000
    options: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BrowserActionResult(BaseModel):
    action_id: str
    success: bool
    result: Optional[Any] = None
    screenshot_base64: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0
    page_url: Optional[str] = None
    page_title: Optional[str] = None


class BrowserSessionConfig(BaseModel):
    viewport_width: int = 1920
    viewport_height: int = 1080
    headless: bool = True
    slow_mo: int = 0
    device_scale_factor: float = 1.0
    user_agent: Optional[str] = None
    locale: str = "en-US"
    timezone: str = "America/New_York"
    color_scheme: Literal["light", "dark", "no-preference"] = "light"
    record_video: bool = False
    video_dir: Optional[str] = None


class BrowserSessionInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    sandbox_id: Optional[str] = None
    status: str = "initializing"
    current_url: Optional[str] = None
    current_title: Optional[str] = None
    config: BrowserSessionConfig = Field(default_factory=BrowserSessionConfig)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_action_at: Optional[datetime] = None
    action_count: int = 0
    error: Optional[str] = None


class ElementInfo(BaseModel):
    tag_name: str
    text: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)
    bounding_box: Optional[Dict[str, float]] = None
    is_visible: bool = True
    is_enabled: bool = True


class PageInfo(BaseModel):
    url: str
    title: str
    viewport: Dict[str, int]
    scroll_position: Dict[str, int]
    content_size: Dict[str, int]


class MCPToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]


class MCPToolResult(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
