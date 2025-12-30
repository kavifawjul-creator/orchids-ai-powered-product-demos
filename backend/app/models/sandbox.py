from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid


class SandboxStatus(str, Enum):
    PENDING = "pending"
    CREATING = "creating"
    CLONING = "cloning"
    INSTALLING = "installing"
    RUNNING = "running"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"
    TERMINATED = "terminated"


class BuildSystem(str, Enum):
    NEXTJS = "nextjs"
    VITE = "vite"
    CREATE_REACT_APP = "create-react-app"
    ANGULAR = "angular"
    VUE = "vue"
    NUXT = "nuxt"
    SVELTE = "svelte"
    REMIX = "remix"
    ASTRO = "astro"
    EXPRESS = "express"
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    RAILS = "rails"
    UNKNOWN = "unknown"


class SandboxConfig(BaseModel):
    language: str = "python"
    env_vars: Dict[str, str] = Field(default_factory=dict)
    auto_stop_interval: int = 30
    auto_archive_interval: int = 60
    timeout_minutes: int = 30
    memory_mb: int = 2048
    cpu_cores: int = 2


class SandboxCreateRequest(BaseModel):
    project_id: str
    git_url: Optional[str] = None
    git_branch: Optional[str] = None
    git_token: Optional[str] = None
    config: SandboxConfig = Field(default_factory=SandboxConfig)


class SandboxInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    daytona_sandbox_id: Optional[str] = None
    status: SandboxStatus = SandboxStatus.PENDING
    preview_url: Optional[str] = None
    preview_port: int = 3000
    build_system: Optional[BuildSystem] = None
    working_dir: str = "/workspace/repo"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BuildDetectionResult(BaseModel):
    build_system: BuildSystem
    install_command: str
    dev_command: str
    build_command: str
    port: int
    confidence: float


class ProcessInfo(BaseModel):
    session_id: str
    command: str
    status: str
    started_at: datetime
    pid: Optional[int] = None


class SandboxResponse(BaseModel):
    success: bool
    sandbox: Optional[SandboxInfo] = None
    message: str = ""
    error: Optional[str] = None
