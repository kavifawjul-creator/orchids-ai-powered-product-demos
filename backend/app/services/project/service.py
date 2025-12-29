import re
import httpx
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from ...models.schemas import Project, ProjectStatus, BuildSystem
from ...core.database import get_supabase
from ...core.events import event_bus, EventTypes
from ...core.config import settings

class ProjectService:
    def __init__(self):
        self.supabase = get_supabase()
    
    async def create_project(self, repo_url: str, title: Optional[str] = None) -> Project:
        validated_url, repo_info = await self._validate_repo(repo_url)
        
        project_title = title or repo_info.get("name", repo_url.split("/")[-1])
        
        project = Project(
            repo_url=validated_url,
            title=project_title,
            description=repo_info.get("description"),
            status=ProjectStatus.PENDING,
            metadata={
                "repo_info": repo_info,
                "created_from": "api"
            }
        )
        
        result = self.supabase.table("projects").insert({
            "id": project.id,
            "repo_url": project.repo_url,
            "title": project.title,
            "description": project.description,
            "status": project.status.value,
            "metadata": project.metadata,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }).execute()
        
        await event_bus.publish(
            f"project:{project.id}",
            EventTypes.PROJECT_CREATED,
            {"project_id": project.id}
        )
        
        return project
    
    async def get_project(self, project_id: str) -> Optional[Project]:
        result = self.supabase.table("projects").select("*").eq("id", project_id).single().execute()
        
        if not result.data:
            return None
            
        return self._row_to_project(result.data)
    
    async def list_projects(self, limit: int = 50, offset: int = 0) -> list[Project]:
        result = self.supabase.table("projects")\
            .select("*")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        return [self._row_to_project(row) for row in result.data]
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Optional[Project]:
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        if "status" in updates and isinstance(updates["status"], ProjectStatus):
            updates["status"] = updates["status"].value
        if "build_system" in updates and isinstance(updates["build_system"], BuildSystem):
            updates["build_system"] = updates["build_system"].value
            
        result = self.supabase.table("projects")\
            .update(updates)\
            .eq("id", project_id)\
            .execute()
        
        if result.data:
            return self._row_to_project(result.data[0])
        return None
    
    async def delete_project(self, project_id: str) -> bool:
        result = self.supabase.table("projects").delete().eq("id", project_id).execute()
        return bool(result.data)
    
    async def detect_build_system(self, files: list[str]) -> Tuple[BuildSystem, Dict[str, Any]]:
        build_config = {}
        
        file_set = set(files)
        
        if "package.json" in file_set:
            build_config["install_command"] = "npm install"
            build_config["dev_command"] = "npm run dev"
            build_config["port"] = 3000
            
            if "next.config.js" in file_set or "next.config.ts" in file_set or "next.config.mjs" in file_set:
                build_config["framework"] = "nextjs"
            elif "vite.config.js" in file_set or "vite.config.ts" in file_set:
                build_config["framework"] = "vite"
                build_config["port"] = 5173
            elif "angular.json" in file_set:
                build_config["framework"] = "angular"
                build_config["port"] = 4200
            else:
                build_config["framework"] = "nodejs"
                
            return BuildSystem.NODEJS, build_config
        
        if "requirements.txt" in file_set or "pyproject.toml" in file_set:
            build_config["install_command"] = "pip install -r requirements.txt"
            build_config["port"] = 8000
            
            if "manage.py" in file_set:
                build_config["framework"] = "django"
                build_config["dev_command"] = "python manage.py runserver"
            elif any("fastapi" in f.lower() for f in files) or "main.py" in file_set:
                build_config["framework"] = "fastapi"
                build_config["dev_command"] = "uvicorn main:app --reload"
            elif any("flask" in f.lower() for f in files) or "app.py" in file_set:
                build_config["framework"] = "flask"
                build_config["dev_command"] = "flask run"
            else:
                build_config["framework"] = "python"
                build_config["dev_command"] = "python app.py"
                
            return BuildSystem.PYTHON, build_config
        
        if "Dockerfile" in file_set:
            build_config["build_command"] = "docker build -t app ."
            build_config["dev_command"] = "docker run -p 3000:3000 app"
            build_config["port"] = 3000
            return BuildSystem.DOCKER, build_config
        
        if "index.html" in file_set:
            build_config["framework"] = "static"
            build_config["dev_command"] = "npx serve ."
            build_config["port"] = 3000
            return BuildSystem.STATIC, build_config
        
        return BuildSystem.UNKNOWN, build_config
    
    async def _validate_repo(self, repo_url: str) -> Tuple[str, Dict[str, Any]]:
        github_pattern = r"(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
        match = re.match(github_pattern, repo_url)
        
        if match:
            owner, repo = match.groups()
            normalized_url = f"https://github.com/{owner}/{repo}"
            
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
                    if response.status_code == 200:
                        data = response.json()
                        return normalized_url, {
                            "name": data.get("name"),
                            "description": data.get("description"),
                            "default_branch": data.get("default_branch", "main"),
                            "private": data.get("private", False),
                            "language": data.get("language"),
                            "stars": data.get("stargazers_count"),
                        }
            except Exception:
                pass
            
            return normalized_url, {"name": repo}
        
        gitlab_pattern = r"(?:https?://)?(?:www\.)?gitlab\.com/([^/]+)/([^/]+?)(?:\.git)?/?$"
        match = re.match(gitlab_pattern, repo_url)
        if match:
            owner, repo = match.groups()
            return f"https://gitlab.com/{owner}/{repo}", {"name": repo}
        
        if repo_url.endswith(".git") or "://" in repo_url:
            return repo_url, {"name": repo_url.split("/")[-1].replace(".git", "")}
        
        raise ValueError(f"Invalid repository URL: {repo_url}")
    
    def _row_to_project(self, row: Dict[str, Any]) -> Project:
        return Project(
            id=row["id"],
            repo_url=row["repo_url"],
            title=row.get("title"),
            description=row.get("description"),
            status=ProjectStatus(row["status"]) if row.get("status") else ProjectStatus.PENDING,
            build_system=BuildSystem(row["build_system"]) if row.get("build_system") else None,
            preview_url=row.get("preview_url"),
            sandbox_id=row.get("sandbox_id"),
            metadata=row.get("metadata", {}),
            created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00")) if row.get("updated_at") else datetime.utcnow()
        )

project_service = ProjectService()
