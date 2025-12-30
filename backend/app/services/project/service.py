import logging
import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse

import httpx
from supabase import create_client, Client

from app.core.config import settings
from app.models.project import (
    ProjectInfo,
    ProjectStatus,
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    GitRepoInfo,
    ProjectAnalysis,
)
from app.services.sandbox import sandbox_service, SandboxCreateRequest, SandboxConfig

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self):
        self._supabase: Optional[Client] = None

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return self._supabase

    def _parse_github_url(self, url: str) -> GitRepoInfo:
        url = url.strip()
        if url.endswith(".git"):
            url = url[:-4]

        patterns = [
            r"github\.com[:/](?P<owner>[^/]+)/(?P<name>[^/]+)",
            r"gitlab\.com[:/](?P<owner>[^/]+)/(?P<name>[^/]+)",
            r"bitbucket\.org[:/](?P<owner>[^/]+)/(?P<name>[^/]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                owner = match.group("owner")
                name = match.group("name")
                return GitRepoInfo(
                    url=url,
                    owner=owner,
                    name=name,
                    clone_url=f"https://github.com/{owner}/{name}.git",
                )

        parsed = urlparse(url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return GitRepoInfo(
                url=url,
                owner=path_parts[0],
                name=path_parts[1],
                clone_url=url if url.endswith(".git") else f"{url}.git",
            )

        return GitRepoInfo(
            url=url,
            owner="unknown",
            name="unknown",
            clone_url=url,
        )

    async def fetch_repo_info(self, url: str, token: Optional[str] = None) -> GitRepoInfo:
        repo_info = self._parse_github_url(url)
        
        if "github.com" in url:
            api_url = f"https://api.github.com/repos/{repo_info.owner}/{repo_info.name}"
            headers = {"Accept": "application/vnd.github.v3+json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(api_url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        repo_info.default_branch = data.get("default_branch", "main")
                        repo_info.branch = repo_info.default_branch
                        repo_info.description = data.get("description")
                        repo_info.language = data.get("language")
                        repo_info.is_private = data.get("private", False)
                        repo_info.topics = data.get("topics", [])
                        repo_info.clone_url = data.get("clone_url", repo_info.clone_url)
            except Exception as e:
                logger.warning(f"Failed to fetch GitHub repo info: {e}")

        return repo_info

    async def create_project(self, request: ProjectCreateRequest) -> ProjectResponse:
        try:
            repo_info = await self.fetch_repo_info(request.repo_url, request.git_token)
            
            title = request.title or repo_info.name
            description = request.description or repo_info.description

            project_data = {
                "repo_url": request.repo_url,
                "title": title,
                "description": description,
                "status": ProjectStatus.PENDING.value,
                "metadata": json.dumps({
                    "branch": request.branch or repo_info.branch,
                    "owner": repo_info.owner,
                    "language": repo_info.language,
                    "topics": repo_info.topics,
                }),
            }

            result = self.supabase.table("projects").insert(project_data).execute()
            
            if not result.data:
                return ProjectResponse(success=False, error="Failed to create project in database")

            project_row = result.data[0]
            project = ProjectInfo(
                id=project_row["id"],
                repo_url=project_row["repo_url"],
                title=project_row["title"],
                description=project_row["description"],
                status=ProjectStatus(project_row["status"]),
                build_system=project_row.get("build_system"),
                preview_url=project_row.get("preview_url"),
                sandbox_id=project_row.get("sandbox_id"),
                metadata=json.loads(project_row["metadata"]) if project_row.get("metadata") else {},
                created_at=datetime.fromisoformat(project_row["created_at"].replace("Z", "+00:00")) if project_row.get("created_at") else datetime.utcnow(),
                updated_at=datetime.fromisoformat(project_row["updated_at"].replace("Z", "+00:00")) if project_row.get("updated_at") else datetime.utcnow(),
            )

            if request.auto_start_sandbox:
                await self._start_sandbox_for_project(project, request.branch, request.git_token)

            return ProjectResponse(
                success=True,
                project=project,
                message="Project created successfully",
            )

        except Exception as e:
            logger.exception(f"Failed to create project: {e}")
            return ProjectResponse(success=False, error=str(e))

    async def _start_sandbox_for_project(
        self,
        project: ProjectInfo,
        branch: Optional[str] = None,
        git_token: Optional[str] = None,
    ):
        try:
            await self.update_project(project.id, ProjectUpdateRequest(
                status=ProjectStatus.SANDBOX_CREATING
            ))

            sandbox_request = SandboxCreateRequest(
                project_id=project.id,
                git_url=project.repo_url,
                git_branch=branch or project.metadata.get("branch"),
                git_token=git_token,
                config=SandboxConfig(language="python"),
            )

            response = await sandbox_service.create_sandbox(sandbox_request)
            
            if response.success and response.sandbox:
                await self.update_project(project.id, ProjectUpdateRequest(
                    status=ProjectStatus.READY,
                    metadata={
                        **project.metadata,
                        "sandbox_id": response.sandbox.id,
                        "preview_url": response.sandbox.preview_url,
                        "build_system": response.sandbox.build_system.value if response.sandbox.build_system else None,
                    }
                ))
                
                self.supabase.table("projects").update({
                    "sandbox_id": response.sandbox.id,
                    "preview_url": response.sandbox.preview_url,
                    "build_system": response.sandbox.build_system.value if response.sandbox.build_system else None,
                }).eq("id", project.id).execute()
            else:
                await self.update_project(project.id, ProjectUpdateRequest(
                    status=ProjectStatus.ERROR,
                    metadata={**project.metadata, "error": response.error}
                ))

        except Exception as e:
            logger.exception(f"Failed to start sandbox for project {project.id}: {e}")
            await self.update_project(project.id, ProjectUpdateRequest(
                status=ProjectStatus.ERROR,
                metadata={**project.metadata, "error": str(e)}
            ))

    async def get_project(self, project_id: str) -> Optional[ProjectInfo]:
        try:
            result = self.supabase.table("projects").select("*").eq("id", project_id).execute()
            
            if not result.data:
                return None

            row = result.data[0]
            return ProjectInfo(
                id=row["id"],
                repo_url=row["repo_url"],
                title=row.get("title"),
                description=row.get("description"),
                status=ProjectStatus(row["status"]) if row.get("status") else ProjectStatus.PENDING,
                build_system=row.get("build_system"),
                preview_url=row.get("preview_url"),
                sandbox_id=row.get("sandbox_id"),
                metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else datetime.utcnow(),
                updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            return None

    async def update_project(self, project_id: str, request: ProjectUpdateRequest) -> ProjectResponse:
        try:
            update_data = {}
            if request.title is not None:
                update_data["title"] = request.title
            if request.description is not None:
                update_data["description"] = request.description
            if request.status is not None:
                update_data["status"] = request.status.value
            if request.metadata is not None:
                update_data["metadata"] = json.dumps(request.metadata)
            
            update_data["updated_at"] = datetime.utcnow().isoformat()

            result = self.supabase.table("projects").update(update_data).eq("id", project_id).execute()
            
            if not result.data:
                return ProjectResponse(success=False, error="Project not found")

            project = await self.get_project(project_id)
            return ProjectResponse(success=True, project=project, message="Project updated")

        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            return ProjectResponse(success=False, error=str(e))

    async def delete_project(self, project_id: str) -> bool:
        try:
            project = await self.get_project(project_id)
            if project and project.sandbox_id:
                await sandbox_service.terminate_sandbox(project.sandbox_id)

            self.supabase.table("projects").delete().eq("id", project_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            return False

    async def list_projects(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[ProjectStatus] = None,
    ) -> List[ProjectInfo]:
        try:
            query = self.supabase.table("projects").select("*")
            
            if status:
                query = query.eq("status", status.value)
            
            result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

            projects = []
            for row in result.data:
                projects.append(ProjectInfo(
                    id=row["id"],
                    repo_url=row["repo_url"],
                    title=row.get("title"),
                    description=row.get("description"),
                    status=ProjectStatus(row["status"]) if row.get("status") else ProjectStatus.PENDING,
                    build_system=row.get("build_system"),
                    preview_url=row.get("preview_url"),
                    sandbox_id=row.get("sandbox_id"),
                    metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else datetime.utcnow(),
                ))
            return projects

        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    async def get_project_sandbox(self, project_id: str):
        project = await self.get_project(project_id)
        if not project or not project.sandbox_id:
            return None
        return await sandbox_service.get_sandbox(project.sandbox_id)


project_service = ProjectService()
