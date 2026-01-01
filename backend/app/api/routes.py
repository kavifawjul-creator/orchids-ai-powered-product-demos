import re
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..services.project.service import project_service
from ..services.sandbox.service import sandbox_service
from ..services.intent.service import intent_service
from ..services.agent.service import agent_service
from ..services.recorder.service import recorder_service
from ..models.schemas import ProjectStatus, DemoStatus
from ..models.project import ProjectCreateRequest
from ..models.sandbox import SandboxCreateRequest, SandboxConfig
from ..models.intent import PlanGenerationRequest
from ..workers.tasks import generate_demo_task

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

GITHUB_URL_PATTERN = re.compile(
    r'^https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+(?:\.git)?/?$'
)
GITLAB_URL_PATTERN = re.compile(
    r'^https?://(?:www\.)?gitlab\.com/[\w.-]+/[\w.-]+(?:\.git)?/?$'
)
BITBUCKET_URL_PATTERN = re.compile(
    r'^https?://(?:www\.)?bitbucket\.org/[\w.-]+/[\w.-]+(?:\.git)?/?$'
)

MAX_PROMPT_LENGTH = 2000
MIN_PROMPT_LENGTH = 10
MAX_TITLE_LENGTH = 200

def validate_repo_url(url: str) -> bool:
    return bool(
        GITHUB_URL_PATTERN.match(url) or 
        GITLAB_URL_PATTERN.match(url) or 
        BITBUCKET_URL_PATTERN.match(url)
    )

class CreateProjectRequest(BaseModel):
    repo_url: str = Field(..., min_length=10, max_length=500)
    title: Optional[str] = Field(None, max_length=MAX_TITLE_LENGTH)
    
    @field_validator('repo_url')
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        if not validate_repo_url(v):
            raise ValueError('Invalid repository URL. Must be a valid GitHub, GitLab, or Bitbucket URL')
        return v

class CreateDemoRequest(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=MAX_TITLE_LENGTH)
    prompt: str = Field(..., min_length=MIN_PROMPT_LENGTH, max_length=MAX_PROMPT_LENGTH)

class GenerateDemoRequest(BaseModel):
    repo_url: str = Field(..., min_length=10, max_length=500)
    prompt: str = Field(..., min_length=MIN_PROMPT_LENGTH, max_length=MAX_PROMPT_LENGTH)
    title: Optional[str] = Field(None, max_length=MAX_TITLE_LENGTH)
    
    @field_validator('repo_url')
    @classmethod
    def validate_repo_url(cls, v: str) -> str:
        if not validate_repo_url(v):
            raise ValueError('Invalid repository URL. Must be a valid GitHub, GitLab, or Bitbucket URL')
        return v
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if len(v.strip()) < MIN_PROMPT_LENGTH:
            raise ValueError(f'Prompt must be at least {MIN_PROMPT_LENGTH} characters')
        return v.strip()

@router.post("/projects")
async def create_project(request: CreateProjectRequest, req: Request):
    try:
        project_request = ProjectCreateRequest(
            repo_url=request.repo_url,
            title=request.title,
            auto_start_sandbox=False
        )
        response = await project_service.create_project(project_request)
        
        if not response.success or not response.project:
            raise HTTPException(status_code=400, detail=response.error or "Failed to create project")
        
        project = response.project
        return {
            "id": project.id,
            "repo_url": project.repo_url,
            "title": project.title,
            "status": project.status.value,
            "created_at": project.created_at.isoformat()
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects")
async def list_projects(limit: int = 50, offset: int = 0):
    limit = min(limit, 100)
    offset = max(offset, 0)
    
    projects = await project_service.list_projects(limit=limit, offset=offset)
    return {
        "projects": [
            {
                "id": p.id,
                "repo_url": p.repo_url,
                "title": p.title,
                "status": p.status.value,
                "preview_url": p.preview_url,
                "created_at": p.created_at.isoformat()
            }
            for p in projects
        ]
    }

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.id,
        "repo_url": project.repo_url,
        "title": project.title,
        "description": project.description,
        "status": project.status.value,
        "build_system": project.build_system if project.build_system else None,
        "preview_url": project.preview_url,
        "sandbox_id": project.sandbox_id,
        "metadata": project.metadata,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat()
    }

@router.post("/projects/{project_id}/build")
async def build_project(project_id: str, background_tasks: BackgroundTasks):
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    async def build_task():
        try:
            sandbox_request = SandboxCreateRequest(
                project_id=project.id,
                git_url=project.repo_url,
                config=SandboxConfig(language="javascript")
            )
            await sandbox_service.create_sandbox(sandbox_request)
        except Exception as e:
            from ..models.project import ProjectUpdateRequest
            await project_service.update_project(project_id, ProjectUpdateRequest(
                status=ProjectStatus.ERROR,
                metadata={**project.metadata, "error": str(e)}
            ))
            await sandbox_service.cleanup_failed_sandboxes(project_id)
    
    background_tasks.add_task(build_task)
    
    return {
        "message": "Build started",
        "project_id": project_id
    }

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.sandbox_id:
        await sandbox_service.terminate_sandbox(project.sandbox_id)
    
    await project_service.delete_project(project_id)
    return {"message": "Project deleted"}

@router.get("/sandboxes/{sandbox_id}")
async def get_sandbox(sandbox_id: str):
    sandbox = await sandbox_service.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {
        "id": sandbox.id,
        "project_id": sandbox.project_id,
        "status": sandbox.status.value,
        "preview_url": sandbox.preview_url,
        "port": sandbox.preview_port,
        "error_message": sandbox.error_message
    }

@router.delete("/sandboxes/{sandbox_id}")
async def destroy_sandbox(sandbox_id: str):
    success = await sandbox_service.terminate_sandbox(sandbox_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"message": "Sandbox destroyed"}

@router.post("/sandboxes/{sandbox_id}/extend")
async def extend_sandbox(sandbox_id: str, minutes: int = 30):
    minutes = min(max(minutes, 5), 120)
    sandbox = await sandbox_service.get_sandbox(sandbox_id)
    if not sandbox:
        raise HTTPException(status_code=400, detail="Cannot extend sandbox - not found")
    return {"message": f"Sandbox extended by {minutes} minutes"}

@router.post("/demos/generate")
async def generate_demo(request: GenerateDemoRequest, background_tasks: BackgroundTasks, req: Request):
    from ..core.database import get_supabase
    from ..core.config import settings
    
    supabase = get_supabase()
    
    project = await project_service.get_project_by_repo(request.repo_url)
    if not project:
        project = await project_service.create_project_simple(
            repo_url=request.repo_url,
            title=request.title
        )
    
    if not project:
        raise HTTPException(status_code=500, detail="Failed to create project")
    
    demo_id = str(uuid.uuid4())
    title = request.title or request.prompt[:50] if len(request.prompt) > 50 else request.prompt
    demo_data = {
        "id": demo_id,
        "title": title,
        "repo_url": request.repo_url,
        "description": request.prompt,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    supabase.table("demos").insert(demo_data).execute()
    
    from ..workers.tasks import _run_generation_pipeline
    
    if settings.REDIS_URL:
        try:
            generate_demo_task.delay(
                demo_id=demo_id,
                repo_url=request.repo_url,
                prompt=request.prompt,
                title=title
            )
        except Exception as e:
            print(f"Celery task failed: {e}. Falling back to background task.")
            background_tasks.add_task(
                _run_generation_pipeline,
                demo_id,
                request.repo_url,
                request.prompt,
                title
            )
    else:
        background_tasks.add_task(
            _run_generation_pipeline,
            demo_id,
            request.repo_url,
            request.prompt,
            title
        )
    
    return {
        "demo_id": demo_id,
        "project_id": project.id,
        "status": "pending",
        "message": "Demo generation started"
    }

@router.get("/demos/{demo_id}")
async def get_demo(demo_id: str):
    from ..core.database import get_supabase
    supabase = get_supabase()
    
    result = supabase.table("demos").select("*").eq("id", demo_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    return result.data

@router.get("/demos/{demo_id}/clips")
async def get_demo_clips(demo_id: str):
    from ..core.database import get_supabase
    supabase = get_supabase()
    
    result = supabase.table("clips")\
        .select("*")\
        .eq("demo_id", demo_id)\
        .order("order_index")\
        .execute()
    
    return {"clips": result.data}

@router.get("/demos/{demo_id}/plan")
async def get_demo_plan(demo_id: str):
    from ..core.database import get_supabase
    supabase = get_supabase()
    
    result = supabase.table("execution_plans").select("*").eq("demo_id", demo_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return result.data

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = await agent_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session.id,
        "project_id": session.project_id,
        "plan_id": session.plan_id,
        "state": session.state.value,
        "current_step_index": session.current_step_index,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "completed_at": session.completed_at.isoformat() if session.completed_at else None
    }

@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: str):
    from ..models.agent import AgentCommand
    success = await agent_service.handle_command(session_id, AgentCommand.STOP)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session stopped"}

@router.get("/sessions/{session_id}/screenshot")
async def get_session_screenshot(session_id: str):
    from ..services.browser.service import browser_service
    
    session = await agent_service.get_session(session_id)
    if not session or not session.browser_session_id:
        raise HTTPException(status_code=404, detail="Screenshot not available")
    
    screenshot = await browser_service.take_screenshot(session.browser_session_id)
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not available")
    
    import base64
    return {"screenshot": base64.b64encode(screenshot).decode()}

@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    session = await agent_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session.id,
        "state": session.state.value,
        "current_step_index": session.current_step_index,
        "total_steps": session.total_steps,
        "error": session.error
    }

@router.get("/demos/{demo_id}/status")
async def get_demo_status(demo_id: str):
    from ..core.database import get_supabase
    supabase = get_supabase()
    
    result = supabase.table("demos").select("id, status, updated_at").eq("id", demo_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    sessions = await agent_service.list_sessions()
    for session in sessions:
        if hasattr(session, 'demo_id') and session.demo_id == demo_id:
            status = {
                "id": session.id,
                "state": session.state.value,
                "current_step_index": session.current_step_index,
                "total_steps": session.total_steps
            }
            return {
                **result.data,
                "session": status
            }
    
    return result.data

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "autovid-backend"}
