import asyncio
import logging
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from daytona_sdk import Daytona, DaytonaConfig
from daytona_sdk.models import CreateSandboxParams

from app.core.config import settings
from app.models.sandbox import (
    SandboxInfo,
    SandboxStatus,
    SandboxConfig,
    SandboxCreateRequest,
    SandboxResponse,
    BuildSystem,
    BuildDetectionResult,
    ProcessInfo,
)

logger = logging.getLogger(__name__)


BUILD_DETECTION_RULES: List[Dict[str, Any]] = [
    {
        "build_system": BuildSystem.NEXTJS,
        "detect_files": ["next.config.js", "next.config.ts", "next.config.mjs"],
        "detect_deps": ["next"],
        "install_command": "npm install",
        "dev_command": "npm run dev",
        "build_command": "npm run build",
        "port": 3000,
    },
    {
        "build_system": BuildSystem.VITE,
        "detect_files": ["vite.config.js", "vite.config.ts"],
        "detect_deps": ["vite"],
        "install_command": "npm install",
        "dev_command": "npm run dev",
        "build_command": "npm run build",
        "port": 5173,
    },
    {
        "build_system": BuildSystem.CREATE_REACT_APP,
        "detect_files": [],
        "detect_deps": ["react-scripts"],
        "install_command": "npm install",
        "dev_command": "npm start",
        "build_command": "npm run build",
        "port": 3000,
    },
    {
        "build_system": BuildSystem.NUXT,
        "detect_files": ["nuxt.config.js", "nuxt.config.ts"],
        "detect_deps": ["nuxt"],
        "install_command": "npm install",
        "dev_command": "npm run dev",
        "build_command": "npm run build",
        "port": 3000,
    },
    {
        "build_system": BuildSystem.VUE,
        "detect_files": ["vue.config.js"],
        "detect_deps": ["vue", "@vue/cli-service"],
        "install_command": "npm install",
        "dev_command": "npm run serve",
        "build_command": "npm run build",
        "port": 8080,
    },
    {
        "build_system": BuildSystem.SVELTE,
        "detect_files": ["svelte.config.js"],
        "detect_deps": ["svelte"],
        "install_command": "npm install",
        "dev_command": "npm run dev",
        "build_command": "npm run build",
        "port": 5173,
    },
    {
        "build_system": BuildSystem.REMIX,
        "detect_files": ["remix.config.js"],
        "detect_deps": ["@remix-run/react"],
        "install_command": "npm install",
        "dev_command": "npm run dev",
        "build_command": "npm run build",
        "port": 3000,
    },
    {
        "build_system": BuildSystem.ASTRO,
        "detect_files": ["astro.config.mjs", "astro.config.js"],
        "detect_deps": ["astro"],
        "install_command": "npm install",
        "dev_command": "npm run dev",
        "build_command": "npm run build",
        "port": 4321,
    },
    {
        "build_system": BuildSystem.EXPRESS,
        "detect_files": [],
        "detect_deps": ["express"],
        "install_command": "npm install",
        "dev_command": "npm start",
        "build_command": "",
        "port": 3000,
    },
    {
        "build_system": BuildSystem.FASTAPI,
        "detect_files": ["main.py", "app/main.py"],
        "detect_deps": ["fastapi"],
        "install_command": "pip install -r requirements.txt",
        "dev_command": "uvicorn main:app --reload --host 0.0.0.0 --port 8000",
        "build_command": "",
        "port": 8000,
    },
    {
        "build_system": BuildSystem.FLASK,
        "detect_files": ["app.py"],
        "detect_deps": ["flask"],
        "install_command": "pip install -r requirements.txt",
        "dev_command": "flask run --host 0.0.0.0 --port 5000",
        "build_command": "",
        "port": 5000,
    },
    {
        "build_system": BuildSystem.DJANGO,
        "detect_files": ["manage.py"],
        "detect_deps": ["django"],
        "install_command": "pip install -r requirements.txt",
        "dev_command": "python manage.py runserver 0.0.0.0:8000",
        "build_command": "",
        "port": 8000,
    },
]


class DaytonaSandboxService:
    def __init__(self):
        self._daytona: Optional[Daytona] = None
        self._sandboxes: Dict[str, SandboxInfo] = {}
        self._event_callbacks: List[Callable] = []

    @property
    def daytona(self) -> Daytona:
        if self._daytona is None:
            config = DaytonaConfig(
                api_key=settings.DAYTONA_API_KEY,
                api_url=settings.DAYTONA_API_URL,
                target=settings.DAYTONA_TARGET,
            )
            self._daytona = Daytona(config)
        return self._daytona

    def register_event_callback(self, callback: Callable):
        self._event_callbacks.append(callback)

    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    async def create_sandbox(self, request: SandboxCreateRequest) -> SandboxResponse:
        sandbox_info = SandboxInfo(
            project_id=request.project_id,
            status=SandboxStatus.CREATING,
        )
        self._sandboxes[sandbox_info.id] = sandbox_info

        try:
            await self._emit_event("SANDBOX_CREATING", {"sandbox_id": sandbox_info.id})
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Creating Daytona sandbox...")

            params = CreateSandboxParams(
                language=request.config.language,
                env_vars=request.config.env_vars,
                auto_stop_interval=request.config.auto_stop_interval,
            )
            sandbox = self.daytona.create(params)
            sandbox_info.daytona_sandbox_id = sandbox.id
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Sandbox created: {sandbox.id}")

            if request.git_url:
                sandbox_info.status = SandboxStatus.CLONING
                sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Cloning repository: {request.git_url}")
                await self._emit_event("SANDBOX_CLONING", {"sandbox_id": sandbox_info.id, "git_url": request.git_url})

                clone_kwargs = {
                    "url": request.git_url,
                    "path": sandbox_info.working_dir,
                }
                if request.git_branch:
                    clone_kwargs["branch"] = request.git_branch
                if request.git_token:
                    clone_kwargs["username"] = "oauth2"
                    clone_kwargs["password"] = request.git_token

                sandbox.git.clone(**clone_kwargs)
                sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Repository cloned successfully")

            build_result = await self._detect_build_system(sandbox, sandbox_info.working_dir)
            sandbox_info.build_system = build_result.build_system
            sandbox_info.preview_port = build_result.port
            sandbox_info.metadata["build_detection"] = build_result.model_dump()
            sandbox_info.logs.append(
                f"[{datetime.utcnow().isoformat()}] Detected build system: {build_result.build_system.value}"
            )

            sandbox_info.status = SandboxStatus.INSTALLING
            await self._emit_event("SANDBOX_INSTALLING", {"sandbox_id": sandbox_info.id})
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Installing dependencies...")

            install_result = sandbox.process.code_run(
                f"cd {sandbox_info.working_dir} && {build_result.install_command}"
            )
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Install output: {install_result.result[:500] if install_result.result else 'OK'}")

            sandbox_info.status = SandboxStatus.RUNNING
            await self._emit_event("SANDBOX_RUNNING", {"sandbox_id": sandbox_info.id})
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Starting dev server...")

            session_id = sandbox.process.create_session()
            sandbox.process.execute_session_command(
                session_id,
                f"cd {sandbox_info.working_dir} && {build_result.dev_command}",
                timeout=5
            )
            sandbox_info.metadata["dev_session_id"] = session_id

            await asyncio.sleep(5)

            preview_link = sandbox.get_preview_link(build_result.port)
            sandbox_info.preview_url = preview_link
            sandbox_info.status = SandboxStatus.READY
            sandbox_info.updated_at = datetime.utcnow()
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Preview URL: {preview_link}")

            await self._emit_event("SANDBOX_READY", {
                "sandbox_id": sandbox_info.id,
                "preview_url": preview_link,
            })

            return SandboxResponse(
                success=True,
                sandbox=sandbox_info,
                message="Sandbox created and running",
            )

        except Exception as e:
            logger.exception(f"Failed to create sandbox: {e}")
            sandbox_info.status = SandboxStatus.ERROR
            sandbox_info.error_message = str(e)
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] ERROR: {str(e)}")
            await self._emit_event("SANDBOX_ERROR", {"sandbox_id": sandbox_info.id, "error": str(e)})

            return SandboxResponse(
                success=False,
                sandbox=sandbox_info,
                error=str(e),
            )

    async def _detect_build_system(self, sandbox, working_dir: str) -> BuildDetectionResult:
        try:
            ls_result = sandbox.process.code_run(f"ls -la {working_dir}")
            files = ls_result.result.split("\n") if ls_result.result else []
            files_lower = [f.lower() for f in files]
        except Exception:
            files_lower = []

        package_json = {}
        try:
            pkg_result = sandbox.process.code_run(f"cat {working_dir}/package.json")
            if pkg_result.result:
                package_json = json.loads(pkg_result.result)
        except Exception:
            pass

        dependencies = {}
        if package_json:
            dependencies.update(package_json.get("dependencies", {}))
            dependencies.update(package_json.get("devDependencies", {}))

        requirements = []
        try:
            req_result = sandbox.process.code_run(f"cat {working_dir}/requirements.txt")
            if req_result.result:
                requirements = [line.split("==")[0].split(">=")[0].strip().lower() for line in req_result.result.split("\n") if line.strip()]
        except Exception:
            pass

        for rule in BUILD_DETECTION_RULES:
            confidence = 0.0
            
            for detect_file in rule.get("detect_files", []):
                if detect_file.lower() in files_lower or any(detect_file.lower() in f for f in files_lower):
                    confidence += 0.5

            for dep in rule.get("detect_deps", []):
                if dep in dependencies:
                    confidence += 0.5
                if dep.lower() in requirements:
                    confidence += 0.5

            if confidence >= 0.5:
                return BuildDetectionResult(
                    build_system=rule["build_system"],
                    install_command=rule["install_command"],
                    dev_command=rule["dev_command"],
                    build_command=rule["build_command"],
                    port=rule["port"],
                    confidence=min(confidence, 1.0),
                )

        return BuildDetectionResult(
            build_system=BuildSystem.UNKNOWN,
            install_command="npm install",
            dev_command="npm start",
            build_command="npm run build",
            port=3000,
            confidence=0.0,
        )

    async def get_sandbox(self, sandbox_id: str) -> Optional[SandboxInfo]:
        return self._sandboxes.get(sandbox_id)

    async def get_sandbox_by_project(self, project_id: str) -> Optional[SandboxInfo]:
        for sandbox in self._sandboxes.values():
            if sandbox.project_id == project_id and sandbox.status == SandboxStatus.READY:
                return sandbox
        return None

    async def execute_command(self, sandbox_id: str, command: str) -> Dict[str, Any]:
        sandbox_info = self._sandboxes.get(sandbox_id)
        if not sandbox_info or not sandbox_info.daytona_sandbox_id:
            return {"success": False, "error": "Sandbox not found"}

        try:
            sandbox = self.daytona.get_current_sandbox(sandbox_info.daytona_sandbox_id)
            result = sandbox.process.code_run(f"cd {sandbox_info.working_dir} && {command}")
            return {
                "success": True,
                "output": result.result,
                "exit_code": result.exit_code if hasattr(result, "exit_code") else 0,
            }
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def upload_file(self, sandbox_id: str, path: str, content: bytes) -> Dict[str, Any]:
        sandbox_info = self._sandboxes.get(sandbox_id)
        if not sandbox_info or not sandbox_info.daytona_sandbox_id:
            return {"success": False, "error": "Sandbox not found"}

        try:
            sandbox = self.daytona.get_current_sandbox(sandbox_info.daytona_sandbox_id)
            full_path = f"{sandbox_info.working_dir}/{path}"
            sandbox.fs.upload_file(full_path, content)
            return {"success": True, "path": full_path}
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_preview_url(self, sandbox_id: str, port: Optional[int] = None) -> Optional[str]:
        sandbox_info = self._sandboxes.get(sandbox_id)
        if not sandbox_info or not sandbox_info.daytona_sandbox_id:
            return None

        try:
            sandbox = self.daytona.get_current_sandbox(sandbox_info.daytona_sandbox_id)
            target_port = port or sandbox_info.preview_port
            return sandbox.get_preview_link(target_port)
        except Exception as e:
            logger.error(f"Failed to get preview URL: {e}")
            return None

    async def stop_sandbox(self, sandbox_id: str) -> bool:
        sandbox_info = self._sandboxes.get(sandbox_id)
        if not sandbox_info or not sandbox_info.daytona_sandbox_id:
            return False

        try:
            sandbox = self.daytona.get_current_sandbox(sandbox_info.daytona_sandbox_id)
            
            if "dev_session_id" in sandbox_info.metadata:
                try:
                    sandbox.process.stop_session(sandbox_info.metadata["dev_session_id"])
                except Exception:
                    pass

            sandbox_info.status = SandboxStatus.STOPPED
            sandbox_info.updated_at = datetime.utcnow()
            await self._emit_event("SANDBOX_STOPPED", {"sandbox_id": sandbox_id})
            return True
        except Exception as e:
            logger.error(f"Failed to stop sandbox: {e}")
            return False

    async def terminate_sandbox(self, sandbox_id: str) -> bool:
        sandbox_info = self._sandboxes.get(sandbox_id)
        if not sandbox_info or not sandbox_info.daytona_sandbox_id:
            return False

        try:
            self.daytona.remove(sandbox_info.daytona_sandbox_id)
            sandbox_info.status = SandboxStatus.TERMINATED
            sandbox_info.updated_at = datetime.utcnow()
            await self._emit_event("SANDBOX_TERMINATED", {"sandbox_id": sandbox_id})
            return True
        except Exception as e:
            logger.error(f"Failed to terminate sandbox: {e}")
            return False

    async def cleanup_expired_sandboxes(self) -> int:
        cleaned = 0
        now = datetime.utcnow()
        timeout_seconds = settings.SANDBOX_TIMEOUT_MINUTES * 60

        for sandbox_id, sandbox_info in list(self._sandboxes.items()):
            elapsed = (now - sandbox_info.created_at).total_seconds()
            if elapsed > timeout_seconds and sandbox_info.status == SandboxStatus.READY:
                if await self.terminate_sandbox(sandbox_id):
                    cleaned += 1
                    logger.info(f"Cleaned up expired sandbox: {sandbox_id}")

        return cleaned

    async def get_all_sandboxes(self) -> List[SandboxInfo]:
        return list(self._sandboxes.values())

    async def get_logs(self, sandbox_id: str) -> List[str]:
        sandbox_info = self._sandboxes.get(sandbox_id)
        if not sandbox_info:
            return []
        return sandbox_info.logs


sandbox_service = DaytonaSandboxService()
