from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class ProjectStatus(str, Enum):
    PENDING = "pending"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    SANDBOX_CREATING = "sandbox_creating"
    READY = "ready"
    ERROR = "error"
    ARCHIVED = "archived"


class ProjectCreateRequest(BaseModel):
    repo_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    branch: Optional[str] = None
    git_token: Optional[str] = None
    auto_start_sandbox: bool = True


class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[Dict[str, Any]] = None


class ProjectInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    repo_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.PENDING
    build_system: Optional[str] = None
    preview_url: Optional[str] = None
    sandbox_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectResponse(BaseModel):
    success: bool
    project: Optional[ProjectInfo] = None
    message: str = ""
    error: Optional[str] = None


class GitRepoInfo(BaseModel):
    url: str
    owner: str
    name: str
    branch: str = "main"
    default_branch: Optional[str] = None
    is_private: bool = False
    clone_url: str = ""
    description: Optional[str] = None
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)


class ProjectAnalysis(BaseModel):
    project_id: str
    repo_info: GitRepoInfo
    detected_framework: Optional[str] = None
    detected_language: str = "unknown"
    has_package_json: bool = False
    has_requirements: bool = False
    entry_points: List[str] = Field(default_factory=list)
    routes: List[str] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    confidence: float = 0.0
