from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class AgentState(str, Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class AgentEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)


class StepExecution(BaseModel):
    step_id: str
    order: int
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    screenshot_before: Optional[str] = None
    screenshot_after: Optional[str] = None
    retries: int = 0


class AgentSessionConfig(BaseModel):
    max_steps: int = 100
    max_retries_per_step: int = 3
    step_timeout_ms: int = 30000
    session_timeout_minutes: int = 15
    auto_screenshot: bool = True
    pause_between_steps_ms: int = 500
    enable_recovery: bool = True


class AgentSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    plan_id: str
    browser_session_id: Optional[str] = None
    state: AgentState = AgentState.IDLE
    config: AgentSessionConfig = Field(default_factory=AgentSessionConfig)
    current_step_index: int = 0
    total_steps: int = 0
    step_executions: List[StepExecution] = Field(default_factory=list)
    events: List[AgentEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentCommand(str, Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    SKIP_STEP = "skip_step"
    RETRY_STEP = "retry_step"


class AgentCommandRequest(BaseModel):
    session_id: str
    command: AgentCommand
    params: Dict[str, Any] = Field(default_factory=dict)


class AgentSessionRequest(BaseModel):
    project_id: str
    plan_id: str
    config: Optional[AgentSessionConfig] = None
    auto_start: bool = True


class AgentSessionResponse(BaseModel):
    success: bool
    session: Optional[AgentSession] = None
    message: str = ""
    error: Optional[str] = None
