import asyncio
import logging
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

_sdk_import_logger = logging.getLogger(__name__)

Daytona = None
DaytonaConfig = None
CreateSandboxParams = None
CreateSandboxBaseParams = None

try:
    from daytona_sdk import Daytona as _Daytona, DaytonaConfig as _DaytonaConfig
    Daytona = _Daytona
    DaytonaConfig = _DaytonaConfig
    _sdk_import_logger.info("Successfully imported Daytona SDK from daytona_sdk")
    try:
        from daytona_sdk import CreateSandboxParams as _CSP
        CreateSandboxParams = _CSP
        CreateSandboxBaseParams = _CSP
    except ImportError:
        try:
            from daytona_sdk import CreateSandboxBaseParams as _CSBP
            CreateSandboxParams = _CSBP
            CreateSandboxBaseParams = _CSBP
        except ImportError:
            _sdk_import_logger.warning("CreateSandboxParams/CreateSandboxBaseParams not found in daytona_sdk")
except ImportError as e:
    _sdk_import_logger.warning(f"Failed to import from daytona_sdk: {e}")
    try:
        from daytona import Daytona as _Daytona, DaytonaConfig as _DaytonaConfig
        Daytona = _Daytona
        DaytonaConfig = _DaytonaConfig
        _sdk_import_logger.info("Successfully imported Daytona SDK from daytona")
        try:
            from daytona import CreateSandboxParams as _CSP
            CreateSandboxParams = _CSP
            CreateSandboxBaseParams = _CSP
        except ImportError:
            try:
                from daytona import CreateSandboxBaseParams as _CSBP
                CreateSandboxParams = _CSBP
                CreateSandboxBaseParams = _CSBP
            except ImportError:
                _sdk_import_logger.warning("CreateSandboxParams/CreateSandboxBaseParams not found in daytona")
    except ImportError as e2:
        _sdk_import_logger.warning(f"Failed to import from daytona: {e2}")

from supabase import Client

from app.core.config import settings
from app.core.database import get_supabase
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
        self._supabase: Optional[Client] = None

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            self._supabase = get_supabase()
        return self._supabase

    async def _persist_sandbox_to_db(self, sandbox_info: SandboxInfo):
        if not sandbox_info.project_id:
            return
        try:
            self.supabase.table("projects").update({
                "sandbox_id": sandbox_info.id,
                "daytona_sandbox_id": sandbox_info.daytona_sandbox_id,
                "sandbox_status": sandbox_info.status.value,
                "sandbox_preview_url": sandbox_info.preview_url,
                "sandbox_created_at": sandbox_info.created_at.isoformat() if sandbox_info.created_at else None,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", sandbox_info.project_id).execute()
            logger.info(f"Persisted sandbox {sandbox_info.id} to DB for project {sandbox_info.project_id}")
        except Exception as e:
            logger.error(f"Failed to persist sandbox to DB: {e}")

    async def _clear_sandbox_from_db(self, project_id: str):
        try:
            self.supabase.table("projects").update({
                "sandbox_id": None,
                "daytona_sandbox_id": None,
                "sandbox_status": "terminated",
                "sandbox_preview_url": None,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", project_id).execute()
            logger.info(f"Cleared sandbox from DB for project {project_id}")
        except Exception as e:
            logger.error(f"Failed to clear sandbox from DB: {e}")

    @property
    def daytona(self):
        if Daytona is None or DaytonaConfig is None:
            logger.warning("Daytona SDK not available - sandbox features disabled")
            return None
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
        await self._persist_sandbox_to_db(sandbox_info)

        try:
            await self._emit_event("SANDBOX_CREATING", {"sandbox_id": sandbox_info.id})
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Creating Daytona sandbox...")

            if self.daytona is None or CreateSandboxParams is None:
                sandbox_info.status = SandboxStatus.ERROR
                sandbox_info.error_message = "Daytona SDK not available"
                await self._persist_sandbox_to_db(sandbox_info)
                return SandboxResponse(
                    success=False,
                    sandbox=sandbox_info,
                    error="Daytona SDK not available - please configure DAYTONA_API_KEY",
                )

            params = CreateSandboxParams(
                language=request.config.language,
                env_vars=request.config.env_vars,
                auto_stop_interval=request.config.auto_stop_interval,
            )
            sandbox = self.daytona.create(params)
            sandbox_info.daytona_sandbox_id = sandbox.id
            sandbox_info.logs.append(f"[{datetime.utcnow().isoformat()}] Sandbox created: {sandbox.id}")
            await self._persist_sandbox_to_db(sandbox_info)

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
            await self._persist_sandbox_to_db(sandbox_info)

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
            await self._persist_sandbox_to_db(sandbox_info)
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
            await self._persist_sandbox_to_db(sandbox_info)
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
            if sandbox_info.project_id:
                await self._clear_sandbox_from_db(sandbox_info.project_id)
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

    async def cleanup_failed_sandboxes(self, project_id: Optional[str] = None) -> int:
        cleaned = 0
        error_statuses = [SandboxStatus.ERROR, SandboxStatus.CREATING]
        now = datetime.utcnow()
        max_error_age_seconds = 300

        for sandbox_id, sandbox_info in list(self._sandboxes.items()):
            if project_id and sandbox_info.project_id != project_id:
                continue
                
            should_cleanup = False
            
            if sandbox_info.status == SandboxStatus.ERROR:
                should_cleanup = True
            elif sandbox_info.status == SandboxStatus.CREATING:
                elapsed = (now - sandbox_info.created_at).total_seconds()
                if elapsed > max_error_age_seconds:
                    should_cleanup = True
            
            if should_cleanup:
                try:
                    if sandbox_info.daytona_sandbox_id and self.daytona:
                        try:
                            self.daytona.remove(sandbox_info.daytona_sandbox_id)
                        except Exception as e:
                            logger.warning(f"Failed to remove Daytona sandbox {sandbox_info.daytona_sandbox_id}: {e}")
                    
                    sandbox_info.status = SandboxStatus.TERMINATED
                    sandbox_info.updated_at = datetime.utcnow()
                    del self._sandboxes[sandbox_id]
                    cleaned += 1
                    logger.info(f"Cleaned up failed sandbox: {sandbox_id} (status was: {sandbox_info.status})")
                    await self._emit_event("SANDBOX_CLEANUP", {"sandbox_id": sandbox_id, "reason": "error"})
                except Exception as e:
                    logger.error(f"Error during cleanup of sandbox {sandbox_id}: {e}")

        return cleaned

    async def cleanup_all_sandboxes(self) -> int:
        cleaned_expired = await self.cleanup_expired_sandboxes()
        cleaned_failed = await self.cleanup_failed_sandboxes()
        return cleaned_expired + cleaned_failed

    async def get_all_sandboxes(self) -> List[SandboxInfo]:
        return list(self._sandboxes.values())

    async def get_logs(self, sandbox_id: str) -> List[str]:
        sandbox_info = self._sandboxes.get(sandbox_id)
        if not sandbox_info:
            return []
        return sandbox_info.logs

    async def recover_sandboxes_from_db(self) -> int:
        recovered = 0
        try:
            result = self.supabase.table("projects").select(
                "id, sandbox_id, daytona_sandbox_id, sandbox_status, sandbox_preview_url, sandbox_created_at"
            ).in_("sandbox_status", ["running", "ready", "creating", "installing", "cloning"]).execute()

            if not result.data:
                logger.info("No active sandboxes to recover from DB")
                return 0

            for row in result.data:
                daytona_id = row.get("daytona_sandbox_id")
                if not daytona_id:
                    continue

                sandbox_exists = False
                if self.daytona:
                    try:
                        self.daytona.get_current_sandbox(daytona_id)
                        sandbox_exists = True
                    except Exception:
                        sandbox_exists = False

                if sandbox_exists:
                    sandbox_info = SandboxInfo(
                        id=row.get("sandbox_id", daytona_id),
                        project_id=row["id"],
                        daytona_sandbox_id=daytona_id,
                        status=SandboxStatus(row.get("sandbox_status", "ready")),
                        preview_url=row.get("sandbox_preview_url"),
                    )
                    if row.get("sandbox_created_at"):
                        try:
                            sandbox_info.created_at = datetime.fromisoformat(row["sandbox_created_at"].replace("Z", "+00:00"))
                        except Exception:
                            pass

                    self._sandboxes[sandbox_info.id] = sandbox_info
                    recovered += 1
                    logger.info(f"Recovered sandbox {sandbox_info.id} for project {row['id']}")
                else:
                    await self._clear_sandbox_from_db(row["id"])
                    logger.info(f"Cleared stale sandbox record for project {row['id']} - Daytona sandbox no longer exists")

            logger.info(f"Sandbox recovery complete: {recovered} sandboxes recovered")
        except Exception as e:
            logger.error(f"Failed to recover sandboxes from DB: {e}")

        return recovered

    async def cleanup_orphaned_sandboxes(self) -> int:
        cleaned = 0
        if not self.daytona:
            return 0

        try:
            db_sandbox_ids = set()
            result = self.supabase.table("projects").select("daytona_sandbox_id").not_.is_("daytona_sandbox_id", "null").execute()
            if result.data:
                db_sandbox_ids = {row["daytona_sandbox_id"] for row in result.data if row.get("daytona_sandbox_id")}

            try:
                daytona_sandboxes = self.daytona.list()
            except Exception as e:
                logger.warning(f"Could not list Daytona sandboxes: {e}")
                return 0

            for sandbox in daytona_sandboxes:
                if sandbox.id not in db_sandbox_ids:
                    try:
                        self.daytona.remove(sandbox.id)
                        cleaned += 1
                        logger.info(f"Cleaned orphaned Daytona sandbox: {sandbox.id}")
                    except Exception as e:
                        logger.warning(f"Failed to remove orphaned sandbox {sandbox.id}: {e}")

            logger.info(f"Orphaned sandbox cleanup complete: {cleaned} sandboxes removed")
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned sandboxes: {e}")

        return cleaned

    async def startup_recovery(self):
        logger.info("Starting sandbox recovery on server startup...")
        recovered = await self.recover_sandboxes_from_db()
        orphaned = await self.cleanup_orphaned_sandboxes()
        logger.info(f"Startup recovery complete: {recovered} recovered, {orphaned} orphaned cleaned")


sandbox_service = DaytonaSandboxService()
