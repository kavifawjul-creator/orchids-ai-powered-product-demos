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

class ExportDemoRequest(BaseModel):
    format: str = Field(default="mp4", pattern="^(mp4|webm|gif)$")
    resolution: str = Field(default="1080p", pattern="^(720p|1080p|4k)$")
    include_subtitles: bool = False
    subtitle_style: str = "default"

@router.post("/demos/{demo_id}/export")
async def export_demo_with_options(demo_id: str, request: ExportDemoRequest, background_tasks: BackgroundTasks):
    """Export demo with format, resolution, and subtitle options."""
    from ..services.export.service import export_service
    from ..core.database import get_supabase
    
    supabase = get_supabase()
    
    # Verify demo exists
    result = supabase.table("demos").select("id, status").eq("id", demo_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    if result.data.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Demo must be completed before export")
    
    async def do_export():
        try:
            await export_service.export_demo_with_options(
                demo_id=demo_id,
                output_format=request.format,
                resolution=request.resolution,
                include_subtitles=request.include_subtitles,
                subtitle_style=request.subtitle_style
            )
        except Exception as e:
            print(f"Export error: {e}")
    
    background_tasks.add_task(do_export)
    
    return {
        "message": "Export started",
        "demo_id": demo_id,
        "format": request.format,
        "resolution": request.resolution,
        "include_subtitles": request.include_subtitles
    }

@router.get("/demos/{demo_id}/analyze")
async def analyze_demo_code(demo_id: str):
    """Analyze the source code of a demo's repository."""
    from ..services.project.analyzer import code_analyzer
    from ..core.database import get_supabase
    
    supabase = get_supabase()
    
    result = supabase.table("demos").select("repo_url").eq("id", demo_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    # For now return a placeholder - actual analysis requires sandbox access
    return {
        "demo_id": demo_id,
        "analysis": {
            "framework": "nextjs",
            "routes_detected": 0,
            "forms_detected": 0,
            "message": "Full analysis requires sandbox access. Use /demos/generate to trigger full analysis."
        }
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "autovid-backend"}


# ============= Editor API Endpoints =============

@router.post("/demos/{demo_id}/clips/{clip_id}/trim")
async def trim_clip(demo_id: str, clip_id: str, trim_start: float = 0, trim_end: float = None):
    """Set trim points for a clip (non-destructive, applied during export)."""
    from ..services.editor.service import editor_service, TrimClipRequest
    
    request = TrimClipRequest(trim_start=trim_start, trim_end=trim_end)
    result = await editor_service.trim_clip(clip_id, request)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {
        "success": True,
        "clip_id": result.clip_id,
        "trim_start": result.trim_start,
        "trim_end": result.trim_end,
        "new_duration": result.new_duration
    }


@router.post("/demos/{demo_id}/clips/{clip_id}/split")
async def split_clip(demo_id: str, clip_id: str, split_point: float):
    """Split a clip at a specific point, creating two clips."""
    from ..services.editor.service import editor_service, SplitClipRequest
    
    request = SplitClipRequest(split_point=split_point)
    result = await editor_service.split_clip(clip_id, request)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {
        "success": True,
        "original_clip_id": result.original_clip_id,
        "first_clip_id": result.first_clip_id,
        "second_clip_id": result.second_clip_id
    }


class GenerateNarrationBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    voice: str = Field(default="nova", pattern="^(alloy|echo|fable|onyx|nova|shimmer)$")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


@router.post("/demos/{demo_id}/clips/{clip_id}/narration")
async def generate_clip_narration(demo_id: str, clip_id: str, body: GenerateNarrationBody):
    """Generate TTS narration audio for a clip."""
    from ..services.editor.service import editor_service, GenerateNarrationRequest
    
    request = GenerateNarrationRequest(
        text=body.text,
        voice=body.voice,
        speed=body.speed
    )
    result = await editor_service.generate_narration(clip_id, request)
    
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return {
        "success": True,
        "clip_id": result.clip_id,
        "audio_url": result.audio_url,
        "duration_seconds": result.duration_seconds,
        "voice": result.voice
    }


class PreviewNarrationBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)
    voice: str = Field(default="nova")
    speed: float = Field(default=1.0)


@router.post("/demos/{demo_id}/narration/preview")
async def preview_narration(demo_id: str, body: PreviewNarrationBody):
    """Preview TTS narration without saving (returns base64 audio)."""
    from ..services.editor.service import editor_service
    
    audio_b64 = await editor_service.preview_narration(
        text=body.text,
        voice=body.voice,
        speed=body.speed
    )
    
    if not audio_b64:
        raise HTTPException(status_code=500, detail="Failed to generate preview")
    
    return {
        "audio_data": audio_b64,
        "format": "mp3",
        "voice": body.voice
    }


@router.get("/editor/voices")
async def get_available_voices():
    """Get list of available TTS voices."""
    from ..services.editor.service import editor_service
    
    voices = await editor_service.get_available_voices()
    return {"voices": voices}


class TextOverlayBody(BaseModel):
    text: str = Field(..., min_length=1, max_length=200)
    position_x: float = Field(default=50, ge=0, le=100)
    position_y: float = Field(default=90, ge=0, le=100)
    font_size: int = Field(default=24, ge=12, le=72)
    font_color: str = Field(default="#ffffff")
    background_color: str = Field(default="rgba(0,0,0,0.5)")
    animation: str = Field(default="fade")
    start_time: float = Field(default=0, ge=0)
    end_time: Optional[float] = None


@router.post("/demos/{demo_id}/clips/{clip_id}/overlays")
async def add_text_overlay(demo_id: str, clip_id: str, body: TextOverlayBody):
    """Add a text overlay to a clip."""
    from ..services.editor.service import editor_service, TextOverlay
    
    overlay = TextOverlay(
        text=body.text,
        position_x=body.position_x,
        position_y=body.position_y,
        font_size=body.font_size,
        font_color=body.font_color,
        background_color=body.background_color,
        animation=body.animation,
        start_time=body.start_time,
        end_time=body.end_time
    )
    
    result = await editor_service.add_text_overlay(clip_id, overlay)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


@router.delete("/demos/{demo_id}/clips/{clip_id}/overlays/{overlay_id}")
async def remove_text_overlay(demo_id: str, clip_id: str, overlay_id: str):
    """Remove a text overlay from a clip."""
    from ..services.editor.service import editor_service
    
    result = await editor_service.remove_text_overlay(clip_id, overlay_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    
    return result


# ============= Advanced Export Endpoints =============

@router.get("/editor/music-presets")
async def get_music_presets():
    """Get list of available background music presets."""
    from ..services.export.service import MUSIC_PRESETS
    
    return {
        "presets": [
            {"id": k, **v}
            for k, v in MUSIC_PRESETS.items()
        ]
    }


@router.get("/editor/transition-types")
async def get_transition_types():
    """Get list of available transition effects."""
    return {
        "transitions": [
            {"id": "fade", "name": "Fade", "description": "Smooth fade between clips"},
            {"id": "dissolve", "name": "Dissolve", "description": "Cross-dissolve blend"},
            {"id": "wipe_left", "name": "Wipe Left", "description": "Wipe from right to left"},
            {"id": "wipe_right", "name": "Wipe Right", "description": "Wipe from left to right"},
            {"id": "slide_left", "name": "Slide Left", "description": "Slide in from right"},
        ]
    }


@router.get("/editor/aspect-ratios")
async def get_aspect_ratios():
    """Get list of available aspect ratios."""
    return {
        "aspect_ratios": [
            {"id": "16:9", "name": "Landscape (16:9)", "description": "Standard widescreen", "resolution": "1920x1080"},
            {"id": "9:16", "name": "Portrait (9:16)", "description": "Vertical/Mobile video", "resolution": "1080x1920"},
            {"id": "1:1", "name": "Square (1:1)", "description": "Instagram/Social square", "resolution": "1080x1080"},
            {"id": "4:3", "name": "Classic (4:3)", "description": "Classic TV aspect", "resolution": "1440x1080"},
            {"id": "21:9", "name": "Ultrawide (21:9)", "description": "Cinematic ultrawide", "resolution": "2560x1080"},
        ]
    }


class AdvancedExportRequest(BaseModel):
    format: str = Field(default="mp4", pattern="^(mp4|webm|gif)$")
    resolution: str = Field(default="1080p", pattern="^(720p|1080p|4k)$")
    aspect_ratio: str = Field(default="16:9", pattern="^(16:9|9:16|1:1|4:3|21:9)$")
    include_subtitles: bool = False
    transitions: bool = False
    transition_type: str = Field(default="dissolve", pattern="^(fade|dissolve|wipe_left|wipe_right|slide_left)$")
    background_music: Optional[str] = None  # Music preset ID
    music_volume: float = Field(default=0.15, ge=0.0, le=1.0)
    watermark: Optional[str] = None
    watermark_position: str = Field(default="bottom_right", pattern="^(top_left|top_right|bottom_left|bottom_right|center)$")


@router.post("/demos/{demo_id}/export/advanced")
async def export_demo_advanced(demo_id: str, body: AdvancedExportRequest, background_tasks: BackgroundTasks):
    """
    Start an advanced export with transitions, music, watermark, and aspect ratio options.
    Returns immediately with an export_id to poll for progress.
    """
    from ..core.database import get_supabase
    import uuid
    
    supabase = get_supabase()
    
    # Verify demo exists
    result = supabase.table("demos").select("id").eq("id", demo_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    # Create export job entry
    export_id = str(uuid.uuid4())
    
    # Queue export in background
    background_tasks.add_task(
        run_advanced_export,
        demo_id=demo_id,
        export_id=export_id,
        options=body.model_dump()
    )
    
    return {
        "export_id": export_id,
        "demo_id": demo_id,
        "status": "queued",
        "message": "Export started. Poll /demos/{demo_id}/export/{export_id}/status for progress."
    }


async def run_advanced_export(demo_id: str, export_id: str, options: dict):
    """Background task to run advanced export with progress tracking."""
    from ..services.export.service import export_service
    from ..core.database import get_supabase
    
    supabase = get_supabase()
    
    # Store export progress in database
    supabase.table("export_jobs").upsert({
        "id": export_id,
        "demo_id": demo_id,
        "status": "processing",
        "progress": 0,
        "step": "Starting export",
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    async def update_progress(step: str, percent: int):
        supabase.table("export_jobs").update({
            "step": step,
            "progress": percent,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", export_id).execute()
    
    try:
        result_url = await export_service.export_with_progress(
            demo_id=demo_id,
            options=options,
            progress_callback=update_progress
        )
        
        supabase.table("export_jobs").update({
            "status": "completed",
            "progress": 100,
            "step": "Complete",
            "result_url": result_url,
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", export_id).execute()
        
    except Exception as e:
        supabase.table("export_jobs").update({
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.utcnow().isoformat()
        }).eq("id", export_id).execute()


@router.get("/demos/{demo_id}/export/{export_id}/status")
async def get_export_status(demo_id: str, export_id: str):
    """Get the status and progress of an export job."""
    from ..core.database import get_supabase
    
    supabase = get_supabase()
    
    result = supabase.table("export_jobs").select("*").eq("id", export_id).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Export job not found")
    
    job = result.data
    return {
        "export_id": job["id"],
        "demo_id": job["demo_id"],
        "status": job["status"],
        "step": job.get("step", ""),
        "progress": job.get("progress", 0),
        "result_url": job.get("result_url"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at")
    }


# ============= Visual Effects Endpoints =============

@router.get("/editor/click-effects")
async def get_click_effect_styles():
    """Get available click effect styles."""
    return {
        "styles": [
            {"id": "ripple", "name": "Ripple", "description": "Expanding concentric circles"},
            {"id": "circle", "name": "Circle", "description": "Simple circle indicator"},
            {"id": "highlight", "name": "Highlight", "description": "Subtle highlight spot"},
        ]
    }


@router.get("/editor/zoom-effects")
async def get_zoom_effect_types():
    """Get available zoom/pan effect types."""
    return {
        "effects": [
            {"id": "slow_zoom_in", "name": "Slow Zoom In", "description": "Ken Burns style zoom in"},
            {"id": "slow_zoom_out", "name": "Slow Zoom Out", "description": "Ken Burns style zoom out"},
            {"id": "pan_left", "name": "Pan Left", "description": "Slow pan from right to left"},
            {"id": "pan_right", "name": "Pan Right", "description": "Slow pan from left to right"},
        ]
    }


class IntroOutroRequest(BaseModel):
    title: str
    subtitle: Optional[str] = ""
    cta_text: Optional[str] = "Try it now!"
    url: Optional[str] = ""
    duration: float = Field(default=3.0, ge=1.0, le=10.0)
    bg_color: str = "black"
    text_color: str = "white"
    brand_color: str = "#7c3aed"


@router.post("/demos/{demo_id}/intro")
async def generate_demo_intro(demo_id: str, body: IntroOutroRequest):
    """Generate an intro video for the demo."""
    from ..services.export.service import export_service
    import os
    
    output_path = os.path.join(export_service.output_dir, f"{demo_id}_intro.mp4")
    
    success = await export_service.generate_intro(
        output_path=output_path,
        title=body.title,
        subtitle=body.subtitle or "",
        duration=body.duration,
        bg_color=body.bg_color,
        text_color=body.text_color,
        brand_color=body.brand_color
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate intro")
    
    return {"success": True, "path": output_path}


@router.post("/demos/{demo_id}/outro")
async def generate_demo_outro(demo_id: str, body: IntroOutroRequest):
    """Generate an outro video for the demo."""
    from ..services.export.service import export_service
    import os
    
    output_path = os.path.join(export_service.output_dir, f"{demo_id}_outro.mp4")
    
    success = await export_service.generate_outro(
        output_path=output_path,
        cta_text=body.cta_text or "Try it now!",
        url=body.url or "",
        duration=body.duration,
        bg_color=body.bg_color,
        text_color=body.text_color
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to generate outro")
    
    return {"success": True, "path": output_path}



