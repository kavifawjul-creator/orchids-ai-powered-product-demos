from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class IntentType(str, Enum):
    EXPLORE = "explore"
    DEMONSTRATE_FEATURE = "demonstrate_feature"
    WALKTHROUGH = "walkthrough"
    COMPARE = "compare"
    ONBOARDING = "onboarding"
    CUSTOM = "custom"


class StepType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    WAIT = "wait"
    SCREENSHOT = "screenshot"
    HOVER = "hover"
    ASSERT = "assert"
    NARRATE = "narrate"


class ExecutionStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order: int
    step_type: StepType
    description: str
    target: Optional[str] = None
    value: Optional[str] = None
    wait_after_ms: int = 500
    screenshot_before: bool = False
    screenshot_after: bool = True
    narration: Optional[str] = None
    expected_outcome: Optional[str] = None
    fallback_steps: List["ExecutionStep"] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FeatureMilestone(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    steps: List[ExecutionStep]
    start_step: int
    end_step: int
    importance: str = "medium"


class ExecutionPlan(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    demo_id: Optional[str] = None
    intent_type: IntentType
    user_prompt: str
    title: str
    description: str
    steps: List[ExecutionStep] = Field(default_factory=list)
    milestones: List[FeatureMilestone] = Field(default_factory=list)
    estimated_duration_seconds: int = 60
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IntentAnalysis(BaseModel):
    intent_type: IntentType
    confidence: float
    features_to_showcase: List[str]
    suggested_routes: List[str]
    key_interactions: List[str]
    target_audience: str = "general"
    tone: str = "professional"
    estimated_steps: int = 10


class PlanGenerationRequest(BaseModel):
    project_id: str
    user_prompt: str
    app_url: str
    app_context: Optional[Dict[str, Any]] = None
    max_steps: int = 50
    include_narration: bool = True
    demo_style: str = "walkthrough"


class PlanGenerationResponse(BaseModel):
    success: bool
    plan: Optional[ExecutionPlan] = None
    intent_analysis: Optional[IntentAnalysis] = None
    error: Optional[str] = None
