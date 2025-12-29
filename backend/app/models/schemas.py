from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class ProjectStatus(str, Enum):
    PENDING = "pending"
    CLONING = "cloning"
    BUILDING = "building"
    READY = "ready"
    ERROR = "error"
    DESTROYED = "destroyed"

class DemoStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

class AgentState(str, Enum):
    INIT = "init"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    RECORDING = "recording"
    FINISHED = "finished"
    ERROR = "error"

class BuildSystem(str, Enum):
    NODEJS = "nodejs"
    PYTHON = "python"
    DOCKER = "docker"
    STATIC = "static"
    UNKNOWN = "unknown"

class Project(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PENDING
    build_system: Optional[BuildSystem] = None
    preview_url: Optional[str] = None
    sandbox_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Demo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    prompt: str
    status: DemoStatus = DemoStatus.PENDING
    execution_plan: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ExecutionStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: str
    target: Optional[str] = None
    value: Optional[str] = None
    reasoning: Optional[str] = None
    success_condition: Optional[str] = None
    timeout_ms: int = 5000

class Feature(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    steps: List[ExecutionStep]
    priority: int = 0

class ExecutionPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    demo_id: str
    video_type: str
    features: List[Feature]
    start_url: str
    estimated_duration_seconds: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    demo_id: str
    project_id: str
    state: AgentState = AgentState.INIT
    current_feature_index: int = 0
    current_step_index: int = 0
    browser_session_id: Optional[str] = None
    events: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

class Clip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    demo_id: str
    feature_id: str
    title: str
    start_time: float
    end_time: float
    duration: str
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    narration: Optional[str] = None
    captions: Optional[str] = None
    overlay: Optional[Dict[str, Any]] = None
    order_index: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RecordingEvent(BaseModel):
    timestamp: float
    event_type: str
    action: Optional[str] = None
    target: Optional[str] = None
    screenshot_path: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BrowserAction(BaseModel):
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    wait_ms: int = 0
