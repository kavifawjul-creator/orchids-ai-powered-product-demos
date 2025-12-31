import asyncio
import uuid
from datetime import datetime
from .celery_app import celery_app
from ..services.project.service import project_service
from ..services.sandbox.service import sandbox_service
from ..services.intent.service import intent_service
from ..services.agent.service import agent_service
from ..services.recorder.service import recorder_service
from ..services.export.service import export_service
from ..core.database import get_supabase
from ..models.sandbox import SandboxCreateRequest, SandboxConfig
from ..models.intent import PlanGenerationRequest
from ..models.agent import AgentSessionRequest

@celery_app.task(name="app.workers.tasks.generate_demo_task")
def generate_demo_task(demo_id: str, repo_url: str, prompt: str, title: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        _run_generation_pipeline(demo_id, repo_url, prompt, title)
    )

async def _run_generation_pipeline(demo_id: str, repo_url: str, prompt: str, title: str):
    supabase = get_supabase()
    
    try:
        supabase.table("demos").update({"status": "building"}).eq("id", demo_id).execute()
        
        project = await project_service.get_project_by_repo(repo_url)
        if not project:
            project = await project_service.create_project_simple(repo_url=repo_url, title=title)
            
        if not project:
            raise Exception("Failed to create or find project")
            
        sandbox_request = SandboxCreateRequest(
            project_id=project.id,
            git_url=repo_url,
            config=SandboxConfig(language="javascript")
        )
        sandbox_response = await sandbox_service.create_sandbox(sandbox_request)
        
        if not sandbox_response.success or not sandbox_response.sandbox:
            raise Exception(f"Failed to create sandbox: {sandbox_response.error}")
            
        sandbox = sandbox_response.sandbox
        if not sandbox.preview_url:
            raise Exception("Failed to get preview URL")
            
        supabase.table("demos").update({"status": "planning"}).eq("id", demo_id).execute()
        
        plan_request = PlanGenerationRequest(
            project_id=project.id,
            user_prompt=prompt,
            app_url=sandbox.preview_url,
            app_context=project.metadata.get("build_config") if project.metadata else None,
            include_narration=True
        )
        plan_response = await intent_service.generate_plan(plan_request)
        
        if not plan_response.success or not plan_response.plan:
            raise Exception(f"Failed to generate plan: {plan_response.error}")
            
        plan = plan_response.plan
        
        supabase.table("demos").update({"status": "executing"}).eq("id", demo_id).execute()
        
        session_request = AgentSessionRequest(
            project_id=project.id,
            plan_id=plan.id,
            auto_start=True
        )
        session_response = await agent_service.create_session(session_request)
        
        if not session_response.success or not session_response.session:
            raise Exception(f"Failed to create agent session: {session_response.error}")
            
        session = session_response.session
        
        await recorder_service.start_recording(session.id, demo_id)
        
        max_wait_time = 300
        wait_interval = 2
        elapsed = 0
        
        while elapsed < max_wait_time:
            current_session = await agent_service.get_session(session.id)
            if not current_session:
                break
            if current_session.state.value in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        await recorder_service.stop_recording(session.id)
        
        for i, milestone in enumerate(plan.milestones):
            await recorder_service.add_milestone(
                session.id,
                milestone.id,
                milestone.name,
                milestone.start_step * 2,
                milestone.end_step * 2
            )
        
        supabase.table("demos").update({"status": "processing"}).eq("id", demo_id).execute()
        clips = await recorder_service.generate_clips(session.id)
        
        final_video_path = await export_service.export_demo(demo_id)
        
        supabase.table("demos").update({
            "status": "completed",
            "video_url": final_video_path,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", demo_id).execute()
        
        return {"status": "success", "demo_id": demo_id, "video_url": final_video_path}
        
    except Exception as e:
        print(f"Generation error: {e}")
        supabase.table("demos").update({
            "status": "error",
            "description": f"Error: {str(e)}",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", demo_id).execute()
        return {"status": "error", "error": str(e)}
