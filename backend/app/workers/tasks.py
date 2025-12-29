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

@celery_app.task(name="app.workers.tasks.generate_demo_task")
def generate_demo_task(demo_id: str, repo_url: str, prompt: str, title: str):
    # Run the async pipeline in the celery worker
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        _run_generation_pipeline(demo_id, repo_url, prompt, title)
    )

async def _run_generation_pipeline(demo_id: str, repo_url: str, prompt: str, title: str):
    supabase = get_supabase()
    
    try:
        # 1. Update status to building
        supabase.table("demos").update({"status": "building"}).eq("id", demo_id).execute()
        
        # 2. Setup project and sandbox
        project = await project_service.get_project_by_repo(repo_url)
        if not project:
            project = await project_service.create_project(repo_url=repo_url, title=title)
            
        sandbox = await sandbox_service.create_sandbox(project)
        if not sandbox.preview_url:
            raise Exception("Failed to get preview URL")
            
        # 3. Planning
        supabase.table("demos").update({"status": "planning"}).eq("id", demo_id).execute()
        plan = await intent_service.generate_execution_plan(
            demo_id=demo_id,
            prompt=prompt,
            app_context=project.metadata.get("build_config")
        )
        
        # 4. Executing & Recording
        supabase.table("demos").update({"status": "executing"}).eq("id", demo_id).execute()
        session = await agent_service.start_session(
            demo_id=demo_id,
            project_id=project.id,
            preview_url=sandbox.preview_url
        )
        
        await recorder_service.start_recording(session.id, demo_id)
        result = await agent_service.execute_plan(session, plan)
        await recorder_service.stop_recording(session.id)
        
        # 5. Process Milestones
        for feature_result in result.get("results", []):
            if "feature_id" in feature_result:
                # In a real scenario, we'd get actual timestamps from the agent/browser
                await recorder_service.add_milestone(
                    session.id,
                    feature_result["feature_id"],
                    feature_result["feature_name"],
                    feature_result.get("start_time", 0),
                    feature_result.get("end_time", 10)
                )
        
        # 6. Generate Clips
        supabase.table("demos").update({"status": "processing"}).eq("id", demo_id).execute()
        clips = await recorder_service.generate_clips(session.id)
        
        # 7. Final Export (Stitching video + audio)
        final_video_path = await export_service.export_demo(demo_id)
        
        # 8. Cleanup
        await agent_service.stop_session(session.id)
        
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
