"""
Static Code Analyzer

Parses repository code to extract routes, components, and UI structure
for better AI planning.
"""

import os
import re
import json
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """
    Analyzes React/Next.js applications to extract:
    - Routes from file structure
    - Interactive UI elements
    - Forms and inputs
    - Navigation patterns
    """
    
    def __init__(self):
        self._route_patterns = {
            "nextjs_app": r"src/app/(.+)/page\.(tsx|jsx|ts|js)",
            "nextjs_pages": r"pages/(.+)\.(tsx|jsx|ts|js)",
            "react_router": r'path=["\']([^"\']+)["\']',
        }
        
        self._component_patterns = {
            "buttons": r'<(?:Button|button)[^>]*>',
            "inputs": r'<(?:Input|input|TextField)[^>]*>',
            "links": r'<(?:Link|a)[^>]*href=["\']([^"\']+)["\']',
            "forms": r'<(?:Form|form)[^>]*>',
        }
    
    async def analyze_repository(
        self,
        repo_path: str,
        framework: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a repository and extract structure information.
        
        Args:
            repo_path: Path to repository root
            framework: Framework type (nextjs, react, vue, etc.)
        
        Returns:
            Dictionary containing routes, components, and metadata
        """
        if not os.path.exists(repo_path):
            logger.error(f"Repository path not found: {repo_path}")
            return {}
        
        # Auto-detect framework if not specified
        if not framework:
            framework = self._detect_framework(repo_path)
        
        result = {
            "framework": framework,
            "routes": [],
            "components": [],
            "forms": [],
            "navigation": [],
            "interactive_elements": []
        }
        
        # Analyze based on framework
        if framework in ["nextjs", "nextjs_app"]:
            result["routes"] = await self._analyze_nextjs_routes(repo_path)
        elif framework == "react":
            result["routes"] = await self._analyze_react_routes(repo_path)
        
        # Find interactive elements across all files
        result["interactive_elements"] = await self._find_interactive_elements(repo_path)
        result["forms"] = await self._find_forms(repo_path)
        
        return result
    
    def _detect_framework(self, repo_path: str) -> str:
        """Detect the framework used in the repository."""
        # Check for Next.js
        if os.path.exists(os.path.join(repo_path, "next.config.js")) or \
           os.path.exists(os.path.join(repo_path, "next.config.ts")) or \
           os.path.exists(os.path.join(repo_path, "next.config.mjs")):
            # Check if using app router
            if os.path.exists(os.path.join(repo_path, "src", "app")) or \
               os.path.exists(os.path.join(repo_path, "app")):
                return "nextjs_app"
            return "nextjs"
        
        # Check for Vue/Nuxt
        if os.path.exists(os.path.join(repo_path, "nuxt.config.js")) or \
           os.path.exists(os.path.join(repo_path, "nuxt.config.ts")):
            return "nuxt"
        
        if os.path.exists(os.path.join(repo_path, "vue.config.js")):
            return "vue"
        
        # Check for React
        package_json = os.path.join(repo_path, "package.json")
        if os.path.exists(package_json):
            try:
                with open(package_json, "r") as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "react" in deps:
                        return "react"
            except:
                pass
        
        return "unknown"
    
    async def _analyze_nextjs_routes(self, repo_path: str) -> List[Dict[str, Any]]:
        """Extract routes from Next.js app router structure."""
        routes = []
        
        # Check both src/app and app directories
        app_dirs = [
            os.path.join(repo_path, "src", "app"),
            os.path.join(repo_path, "app"),
        ]
        
        for app_dir in app_dirs:
            if not os.path.exists(app_dir):
                continue
            
            for root, dirs, files in os.walk(app_dir):
                # Filter out special directories
                dirs[:] = [d for d in dirs if not d.startswith("_") and not d.startswith(".")]
                
                for file in files:
                    if file.startswith("page.") and file.endswith((".tsx", ".jsx", ".ts", ".js")):
                        # Calculate route from path
                        rel_path = os.path.relpath(root, app_dir)
                        route = "/" if rel_path == "." else "/" + rel_path.replace("\\", "/")
                        
                        # Handle dynamic routes
                        route = re.sub(r'\[([^\]]+)\]', r':\1', route)
                        
                        # Analyze page component for details
                        page_path = os.path.join(root, file)
                        page_info = await self._analyze_page_component(page_path)
                        
                        routes.append({
                            "path": route,
                            "file": page_path,
                            "type": "page",
                            "has_layout": os.path.exists(os.path.join(root, "layout.tsx")) or \
                                          os.path.exists(os.path.join(root, "layout.jsx")),
                            **page_info
                        })
        
        return routes
    
    async def _analyze_react_routes(self, repo_path: str) -> List[Dict[str, Any]]:
        """Extract routes from React Router configuration."""
        routes = []
        
        # Look for route definitions in common files
        route_files = [
            "src/routes.tsx", "src/routes.jsx", "src/routes.js",
            "src/App.tsx", "src/App.jsx", "src/App.js",
            "src/router/index.tsx", "src/router/index.jsx",
        ]
        
        for route_file in route_files:
            file_path = os.path.join(repo_path, route_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Find React Router path definitions
                    for match in re.finditer(r'path=["\']([^"\']+)["\']', content):
                        routes.append({
                            "path": match.group(1),
                            "file": file_path,
                            "type": "route"
                        })
                except:
                    pass
        
        return routes
    
    async def _analyze_page_component(self, file_path: str) -> Dict[str, Any]:
        """Analyze a page component file for UI elements."""
        result = {
            "title": None,
            "has_form": False,
            "interactive_count": 0,
            "imports": []
        }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract title from metadata or component
            title_match = re.search(r'title:\s*["\']([^"\']+)["\']', content)
            if title_match:
                result["title"] = title_match.group(1)
            
            # Check for forms
            result["has_form"] = bool(re.search(r'<(?:Form|form)', content))
            
            # Count interactive elements
            buttons = len(re.findall(r'<(?:Button|button)', content, re.IGNORECASE))
            inputs = len(re.findall(r'<(?:Input|input|TextField)', content, re.IGNORECASE))
            links = len(re.findall(r'<(?:Link|a)', content, re.IGNORECASE))
            result["interactive_count"] = buttons + inputs + links
            
            # Extract imports
            for match in re.finditer(r'import\s+.+\s+from\s+["\']([^"\']+)["\']', content):
                result["imports"].append(match.group(1))
            
        except Exception as e:
            logger.debug(f"Failed to analyze {file_path}: {e}")
        
        return result
    
    async def _find_interactive_elements(self, repo_path: str) -> List[Dict[str, Any]]:
        """Find all interactive UI elements across the codebase."""
        elements = []
        
        src_dirs = [
            os.path.join(repo_path, "src"),
            os.path.join(repo_path, "app"),
            os.path.join(repo_path, "components"),
        ]
        
        for src_dir in src_dirs:
            if not os.path.exists(src_dir):
                continue
            
            for root, dirs, files in os.walk(src_dir):
                dirs[:] = [d for d in dirs if not d.startswith("_") and not d.startswith(".") and d != "node_modules"]
                
                for file in files:
                    if not file.endswith((".tsx", ".jsx")):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # Find buttons with text/labels
                        for match in re.finditer(r'<Button[^>]*>([^<]+)</Button>', content):
                            elements.append({
                                "type": "button",
                                "text": match.group(1).strip(),
                                "file": file_path
                            })
                        
                        # Find inputs with placeholders
                        for match in re.finditer(r'<Input[^>]*placeholder=["\']([^"\']+)["\']', content):
                            elements.append({
                                "type": "input",
                                "placeholder": match.group(1),
                                "file": file_path
                            })
                        
                    except:
                        pass
        
        return elements[:50]  # Limit to top 50
    
    async def _find_forms(self, repo_path: str) -> List[Dict[str, Any]]:
        """Find form components in the codebase."""
        forms = []
        
        src_dirs = [
            os.path.join(repo_path, "src"),
            os.path.join(repo_path, "app"),
        ]
        
        for src_dir in src_dirs:
            if not os.path.exists(src_dir):
                continue
            
            for root, dirs, files in os.walk(src_dir):
                dirs[:] = [d for d in dirs if d != "node_modules" and not d.startswith(".")]
                
                for file in files:
                    if not file.endswith((".tsx", ".jsx")):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        if "<form" in content.lower() or "useForm" in content:
                            # Extract form fields
                            fields = []
                            for match in re.finditer(r'name=["\']([^"\']+)["\']', content):
                                fields.append(match.group(1))
                            
                            forms.append({
                                "file": file_path,
                                "fields": fields[:10],  # Limit fields
                                "has_validation": "schema" in content.lower() or "zodResolver" in content
                            })
                    except:
                        pass
        
        return forms
    
    def generate_planning_context(self, analysis: Dict[str, Any]) -> str:
        """
        Generate context string for AI planning from analysis results.
        
        This can be passed to the intent service to improve plan generation.
        """
        context_parts = [
            f"Framework: {analysis.get('framework', 'unknown')}",
            f"Total Routes: {len(analysis.get('routes', []))}",
            f"Total Forms: {len(analysis.get('forms', []))}",
        ]
        
        # Add route summary
        routes = analysis.get("routes", [])
        if routes:
            context_parts.append("\nAvailable Routes:")
            for route in routes[:10]:
                title = route.get("title", route["path"])
                context_parts.append(f"  - {route['path']}: {title}")
        
        # Add form summary
        forms = analysis.get("forms", [])
        if forms:
            context_parts.append("\nForms Found:")
            for form in forms[:5]:
                context_parts.append(f"  - {os.path.basename(form['file'])}: {len(form.get('fields', []))} fields")
        
        # Add interactive elements
        elements = analysis.get("interactive_elements", [])
        if elements:
            context_parts.append(f"\nInteractive Elements: {len(elements)} total")
            buttons = [e for e in elements if e["type"] == "button"]
            if buttons:
                context_parts.append(f"  Buttons: {', '.join(b['text'] for b in buttons[:5])}")
        
        return "\n".join(context_parts)


# Global instance
code_analyzer = CodeAnalyzer()
