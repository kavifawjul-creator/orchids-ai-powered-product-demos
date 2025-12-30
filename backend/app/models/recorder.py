from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class RecordingStatus(str, Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class FrameData(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sequence: int
    timestamp: datetime
    screenshot_base64: str
    page_url: str
    page_title: Optional[str] = None
    action_id: Optional[str] = None
    action_type: Optional[str] = None
    duration_ms: int = 0


class ActionTimelineEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sequence: int
    action_type: str
    description: str
    start_time_ms: int
    end_time_ms: int
    frame_start: int
    frame_end: int
    narration: Optional[str] = None
    is_milestone: bool = False
    milestone_name: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Recording(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    project_id: str
    status: RecordingStatus = RecordingStatus.IDLE
    frames: List[FrameData] = Field(default_factory=list)
    timeline: List[ActionTimelineEntry] = Field(default_factory=list)
    fps: int = 10
    total_duration_ms: int = 0
    frame_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClipBoundary(BaseModel):
    start_frame: int
    end_frame: int
    start_time_ms: int
    end_time_ms: int
    confidence: float = 1.0
    reason: str = ""


class Clip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recording_id: str
    demo_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    order: int
    boundary: ClipBoundary
    frames: List[FrameData] = Field(default_factory=list)
    timeline_entries: List[ActionTimelineEntry] = Field(default_factory=list)
    duration_ms: int = 0
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecorderConfig(BaseModel):
    fps: int = 10
    capture_on_action: bool = True
    capture_interval_ms: int = 100
    max_frames: int = 5000
    auto_clip_on_milestone: bool = True
    min_clip_duration_ms: int = 2000
