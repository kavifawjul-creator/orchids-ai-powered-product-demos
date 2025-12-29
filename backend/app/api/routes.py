from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from ..services.project.service import project_service
from ..services.sandbox.service import sandbox_service
from ..services.intent.service import intent_service
from ..services.agent.service import agent_service
from ..services.recorder.service import recorder_service
from ..models.schemas import ProjectStatus, DemoStatus
from ..workers.tasks import generate_demo_task

router = APIRouter()

class CreateProjectRequest(BaseModel):
    repo_url: str
    title: Optional[str] = None

class CreateDemoRequest(BaseModel):
    project_id: str
    title: str
    prompt: str

class GenerateDemoRequest(BaseModel):
    repo_url: str
    prompt: str
    title: Optional[str] = None

@router.post("/projects")
async def create_project(request: CreateProjectRequest):
    try:
        project = await project_service.create_project(
            repo_url=request.repo_url,
            title=request.title
        )
        return {
            "id": project.id,
            "repo_url": project.repo_url,
            "title": project.title,
            "status": project.status.value,
            "created_at": project.created_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects")
async def list_projects(limit: int = 50, offset: int = 0):
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
        "build_system": project.build_system.value if project.build_system else None,
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
            await sandbox_service.create_sandbox(project)
        except Exception as e:
            await project_service.update_project(project_id, {
                "status": ProjectStatus.ERROR,
                "metadata": {**project.metadata, "error": str(e)}
            })
    
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
        await sandbox_service.destroy_sandbox(project.sandbox_id)
    
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
        "port": sandbox.port,
        "error_message": sandbox.error_message
    }

@router.delete("/sandboxes/{sandbox_id}")
async def destroy_sandbox(sandbox_id: str):
    success = await sandbox_service.destroy_sandbox(sandbox_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return {"message": "Sandbox destroyed"}

@router.post("/sandboxes/{sandbox_id}/extend")
async def extend_sandbox(sandbox_id: str, minutes: int = 30):
    success = await sandbox_service.extend_sandbox(sandbox_id, minutes)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot extend sandbox")
    return {"message": f"Sandbox extended by {minutes} minutes"}

@router.post("/demos/generate")
async def generate_demo(request: GenerateDemoRequest, background_tasks: BackgroundTasks):
    from ..core.database import get_supabase
    import uuid
    from datetime import datetime
    
    supabase = get_supabase()
    
    # 1. Check if project already exists
    project = await project_service.get_project_by_repo(request.repo_url)
    if not project:
        project = await project_service.create_project(
            repo_url=request.repo_url,
            title=request.title
        )
    
    # 2. Create demo record
    demo_id = str(uuid.uuid4())
    demo_data = {
        "id": demo_id,
        "title": request.title or request.prompt[:50],
        "repo_url": request.repo_url,
        "description": request.prompt,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    supabase.table("demos").insert(demo_data).execute()
    
    # 3. Trigger Celery task
    try:
        generate_demo_task.delay(
            demo_id=demo_id,
            repo_url=request.repo_url,
            prompt=request.prompt,
            title=request.title or request.prompt[:50]
        )
    except Exception as e:
        print(f"Failed to enqueue celery task: {e}. Falling back to background task.")
        # Fallback to background task if celery is not available
        from ..workers.tasks import _run_generation_pipeline
        background_tasks.add_task(
            _run_generation_pipeline,
            demo_id,
            request.repo_url,
            request.prompt,
            request.title or request.prompt[:50]
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
    plan = await intent_service.get_plan(demo_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {
        "id": plan.id,
        "demo_id": plan.demo_id,
        "video_type": plan.video_type,
        "features": [
            {
                "id": f.id,
                "name": f.name,
                "description": f.description,
                "priority": f.priority,
                "steps": [
                    {
                        "id": s.id,
                        "action": s.action,
                        "target": s.target,
                        "value": s.value,
                        "reasoning": s.reasoning
                    }
                    for s in f.steps
                ]
            }
            for f in plan.features
        ],
        "start_url": plan.start_url,
        "estimated_duration_seconds": plan.estimated_duration_seconds
    }

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    session = await agent_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "id": session.id,
        "demo_id": session.demo_id,
        "project_id": session.project_id,
        "state": session.state.value,
        "current_feature_index": session.current_feature_index,
        "current_step_index": session.current_step_index,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "finished_at": session.finished_at.isoformat() if session.finished_at else None
    }

@router.post("/sessions/{session_id}/stop")
async def stop_session(session_id: str):
    success = await agent_service.stop_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session stopped"}

@router.get("/sessions/{session_id}/screenshot")
async def get_session_screenshot(session_id: str):
    from ..services.browser.service import browser_service
    
    screenshot = await browser_service.get_screenshot(session_id)
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not available")
    
    return {"screenshot": screenshot}

@router.get("/sessions/{session_id}/status")
async def get_session_status(session_id: str):
    status = await agent_service.get_session_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status

@router.get("/demos/{demo_id}/status")
async def get_demo_status(demo_id: str):
    from ..core.database import get_supabase
    supabase = get_supabase()
    
    result = supabase.table("demos").select("id, status, updated_at").eq("id", demo_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Demo not found")
    
    for session_id, session in agent_service._sessions.items():
        if session.demo_id == demo_id:
            status = await agent_service.get_session_status(session_id)
            return {
                **result.data,
                "session": status
            }
    
    return result.data

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "autovid-backend"}
