import asyncio
import subprocess
import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from ...models.schemas import Project, ProjectStatus, BuildSystem
from ...core.events import event_bus, EventTypes
from ...core.config import settings
from ..project.service import project_service

class SandboxStatus(str, Enum):
    CREATING = "creating"
    CLONING = "cloning"
    BUILDING = "building"
    RUNNING = "running"
    READY = "ready"
    ERROR = "error"
    STOPPED = "stopped"
    DESTROYED = "destroyed"

@dataclass
class SandboxInfo:
    id: str
    project_id: str
    status: SandboxStatus
    preview_url: Optional[str] = None
    workspace_name: Optional[str] = None
    port: int = 3000
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

class SandboxService:
    def __init__(self):
        self._sandboxes: Dict[str, SandboxInfo] = {}
        self._cleanup_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_sandbox(self, project: Project) -> SandboxInfo:
        sandbox_id = f"sandbox-{project.id[:8]}"
        workspace_name = f"autovid-{project.id[:8]}"
        
        sandbox = SandboxInfo(
            id=sandbox_id,
            project_id=project.id,
            status=SandboxStatus.CREATING,
            workspace_name=workspace_name,
            metadata={}
        )
        self._sandboxes[sandbox_id] = sandbox
        
        await event_bus.publish(
            f"sandbox:{sandbox_id}",
            EventTypes.SANDBOX_CREATED,
            {"sandbox_id": sandbox_id, "project_id": project.id}
        )
        
        try:
            sandbox.status = SandboxStatus.CLONING
            await self._clone_repo(sandbox, project)
            
            files = await self._list_files(sandbox)
            build_system, build_config = await project_service.detect_build_system(files)
            
            sandbox.port = build_config.get("port", 3000)
            sandbox.metadata["build_config"] = build_config
            sandbox.metadata["build_system"] = build_system.value
            
            await project_service.update_project(project.id, {
                "build_system": build_system,
                "metadata": {**project.metadata, "build_config": build_config}
            })
            
            sandbox.status = SandboxStatus.BUILDING
            await self._build_app(sandbox, build_config)
            
            sandbox.status = SandboxStatus.RUNNING
            preview_url = await self._start_app(sandbox, build_config)
            sandbox.preview_url = preview_url
            
            await self._wait_for_app(sandbox)
            
            sandbox.status = SandboxStatus.READY
            
            await project_service.update_project(project.id, {
                "status": ProjectStatus.READY,
                "sandbox_id": sandbox_id,
                "preview_url": preview_url
            })
            
            await event_bus.publish(
                f"sandbox:{sandbox_id}",
                EventTypes.SANDBOX_READY,
                {"sandbox_id": sandbox_id, "preview_url": preview_url}
            )
            
            self._schedule_cleanup(sandbox_id, settings.SANDBOX_TIMEOUT_MINUTES * 60)
            
            return sandbox
            
        except Exception as e:
            sandbox.status = SandboxStatus.ERROR
            sandbox.error_message = str(e)
            
            await project_service.update_project(project.id, {
                "status": ProjectStatus.ERROR,
                "metadata": {**project.metadata, "error": str(e)}
            })
            
            await event_bus.publish(
                f"sandbox:{sandbox_id}",
                EventTypes.SANDBOX_ERROR,
                {"sandbox_id": sandbox_id, "error": str(e)}
            )
            
            raise
    
    async def get_sandbox(self, sandbox_id: str) -> Optional[SandboxInfo]:
        return self._sandboxes.get(sandbox_id)
    
    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return False
        
        try:
            if settings.DAYTONA_API_KEY:
                await self._daytona_destroy_workspace(sandbox.workspace_name)
            
            sandbox.status = SandboxStatus.DESTROYED
            
            await project_service.update_project(sandbox.project_id, {
                "status": ProjectStatus.DESTROYED,
                "sandbox_id": None,
                "preview_url": None
            })
            
            await event_bus.publish(
                f"sandbox:{sandbox_id}",
                EventTypes.SANDBOX_DESTROYED,
                {"sandbox_id": sandbox_id}
            )
            
            if sandbox_id in self._cleanup_tasks:
                self._cleanup_tasks[sandbox_id].cancel()
                del self._cleanup_tasks[sandbox_id]
            
            del self._sandboxes[sandbox_id]
            return True
            
        except Exception as e:
            sandbox.error_message = str(e)
            return False
    
    async def extend_sandbox(self, sandbox_id: str, minutes: int = 30) -> bool:
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox or sandbox.status != SandboxStatus.READY:
            return False
        
        if sandbox_id in self._cleanup_tasks:
            self._cleanup_tasks[sandbox_id].cancel()
        
        self._schedule_cleanup(sandbox_id, minutes * 60)
        return True
    
    async def execute_command(self, sandbox_id: str, command: str) -> Dict[str, Any]:
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            raise ValueError(f"Sandbox {sandbox_id} not found")
        
        if settings.DAYTONA_API_KEY:
            return await self._daytona_execute(sandbox.workspace_name, command)
        else:
            return await self._local_execute(command)
    
    async def _clone_repo(self, sandbox: SandboxInfo, project: Project):
        if settings.DAYTONA_API_KEY:
            await self._daytona_create_workspace(sandbox, project)
        else:
            sandbox.metadata["local_path"] = f"/tmp/autovid/{sandbox.id}"
    
    async def _list_files(self, sandbox: SandboxInfo) -> list[str]:
        if settings.DAYTONA_API_KEY:
            return await self._daytona_list_files(sandbox.workspace_name)
        else:
            return [
                "package.json",
                "next.config.ts",
                "src/app/page.tsx",
                "tsconfig.json"
            ]
    
    async def _build_app(self, sandbox: SandboxInfo, build_config: Dict[str, Any]):
        install_cmd = build_config.get("install_command", "npm install")
        await self.execute_command(sandbox.id, install_cmd)
    
    async def _start_app(self, sandbox: SandboxInfo, build_config: Dict[str, Any]) -> str:
        dev_cmd = build_config.get("dev_command", "npm run dev")
        
        if settings.DAYTONA_API_KEY:
            preview_url = f"https://{sandbox.workspace_name}.daytona.app"
        else:
            preview_url = f"http://localhost:{sandbox.port}"
        
        return preview_url
    
    async def _wait_for_app(self, sandbox: SandboxInfo, timeout: int = 60):
        start = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        sandbox.preview_url,
                        timeout=5,
                        follow_redirects=True
                    )
                    if response.status_code < 500:
                        return
            except Exception:
                pass
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"App failed to start within {timeout} seconds")
    
    def _schedule_cleanup(self, sandbox_id: str, delay_seconds: int):
        async def cleanup():
            await asyncio.sleep(delay_seconds)
            await self.destroy_sandbox(sandbox_id)
        
        task = asyncio.create_task(cleanup())
        self._cleanup_tasks[sandbox_id] = task
    
    async def _daytona_create_workspace(self, sandbox: SandboxInfo, project: Project):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DAYTONA_API_URL}/workspaces",
                headers={"Authorization": f"Bearer {settings.DAYTONA_API_KEY}"},
                json={
                    "name": sandbox.workspace_name,
                    "image": "node:20",
                    "cpu": 2,
                    "memory": "4Gi",
                    "git_url": project.repo_url
                }
            )
            response.raise_for_status()
            data = response.json()
            sandbox.metadata["daytona_workspace_id"] = data.get("id")
    
    async def _daytona_destroy_workspace(self, workspace_name: str):
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{settings.DAYTONA_API_URL}/workspaces/{workspace_name}",
                headers={"Authorization": f"Bearer {settings.DAYTONA_API_KEY}"}
            )
            response.raise_for_status()
    
    async def _daytona_execute(self, workspace_name: str, command: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DAYTONA_API_URL}/workspaces/{workspace_name}/exec",
                headers={"Authorization": f"Bearer {settings.DAYTONA_API_KEY}"},
                json={"command": command}
            )
            response.raise_for_status()
            return response.json()
    
    async def _daytona_list_files(self, workspace_name: str) -> list[str]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.DAYTONA_API_URL}/workspaces/{workspace_name}/files",
                headers={"Authorization": f"Bearer {settings.DAYTONA_API_KEY}"}
            )
            response.raise_for_status()
            return response.json().get("files", [])
    
    async def _local_execute(self, command: str) -> Dict[str, Any]:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }

sandbox_service = SandboxService()
