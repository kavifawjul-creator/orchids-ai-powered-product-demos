import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from ...models.schemas import (
    AgentSession, AgentState, ExecutionPlan, Feature, ExecutionStep,
    BrowserAction, DemoStatus
)
from ...core.events import event_bus, EventTypes
from ...core.config import settings
from ...core.database import get_supabase
from ..browser.service import browser_service, BrowserSession
from ..mcp.server import mcp

REASONING_PROMPT = """You are an AI agent executing a browser automation step.

Current step to execute:
- Action: {action}
- Target: {target}
- Value: {value}
- Expected: {success_condition}

Page accessibility snapshot:
{accessibility_tree}

Based on the page state, provide the exact tool to call and its arguments.
Available tools: navigate, click, type_text, hover, scroll, wait, screenshot.

Output JSON:
{{
  "tool": "tool_name",
  "arguments": {{
    "arg_name": "arg_value"
  }},
  "reasoning": "why this action"
}}
"""

VISION_VERIFICATION_PROMPT = """You are an AI agent verifying if a browser action was successful.

Action performed: {action}
Target: {target}
Expected outcome: {expected}

Analyze this screenshot and determine:
1. Was the action successful?
2. What is the current state of the page?
3. Any errors or unexpected behavior?

Output JSON:
{{
  "success": true|false,
  "confidence": 0.0-1.0,
  "current_state": "description of what you see",
  "errors": ["any visible errors"],
  "next_suggestion": "what to do if failed"
}}
"""

class AgentExecutionService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.supabase = get_supabase()
        self._sessions: Dict[str, AgentSession] = {}
        self._broadcast_callbacks: Dict[str, Any] = {}
    
    def set_broadcast_callback(self, session_id: str, callback):
        self._broadcast_callbacks[session_id] = callback
    
    async def _broadcast(self, session_id: str, event_type: str, data: dict):
        if session_id in self._broadcast_callbacks:
            await self._broadcast_callbacks[session_id](event_type, data)
        
        await event_bus.publish(
            f"agent:{session_id}",
            event_type,
            data
        )
    
    async def start_session(
        self,
        demo_id: str,
        project_id: str,
        preview_url: str
    ) -> AgentSession:
        session = AgentSession(
            demo_id=demo_id,
            project_id=project_id,
            state=AgentState.INIT,
            started_at=datetime.utcnow()
        )
        
        self._sessions[session.id] = session
        
        browser_session = await browser_service.create_session(
            session.id,
            headless=True
        )
        session.browser_session_id = browser_session.session_id
        
        await browser_session.navigate(preview_url)
        
        await self._update_demo_status(demo_id, DemoStatus.EXECUTING)
        
        await self._broadcast(session.id, EventTypes.AGENT_STARTED, {
            "session_id": session.id,
            "demo_id": demo_id,
            "preview_url": preview_url
        })
        
        return session
    
    async def execute_plan(
        self,
        session: AgentSession,
        plan: ExecutionPlan
    ) -> Dict[str, Any]:
        session.state = AgentState.EXECUTING
        results = []
        
        browser_session = await browser_service.get_session(session.browser_session_id)
        if not browser_session:
            raise ValueError("Browser session not found")
        
        sorted_features = sorted(plan.features, key=lambda f: f.priority)
        
        for feature_idx, feature in enumerate(sorted_features):
            session.current_feature_index = feature_idx
            feature_start_time = asyncio.get_event_loop().time()
            
            await self._broadcast(session.id, "FEATURE_START", {
                "session_id": session.id,
                "feature_name": feature.name,
                "feature_index": feature_idx,
                "total_features": len(sorted_features),
                "steps_count": len(feature.steps)
            })
            
            feature_result = {
                "feature_id": feature.id,
                "feature_name": feature.name,
                "steps": [],
                "success": True
            }
            
            for step_idx, step in enumerate(feature.steps):
                session.current_step_index = step_idx
                
                await self._broadcast(session.id, "STEP_START", {
                    "session_id": session.id,
                    "feature_name": feature.name,
                    "step_index": step_idx,
                    "total_steps": len(feature.steps),
                    "action": step.action,
                    "target": step.target,
                    "reasoning": step.reasoning
                })
                
                try:
                    step_result = await self._execute_step_with_verification(
                        browser_session,
                        step,
                        feature.name,
                        session.id
                    )
                    
                    feature_result["steps"].append({
                        "step_id": step.id,
                        "action": step.action,
                        "success": step_result.get("success", False),
                        "result": step_result
                    })
                    
                    session.events.append({
                        "timestamp": asyncio.get_event_loop().time(),
                        "type": "step_completed",
                        "feature": feature.name,
                        "step": step.action,
                        "success": step_result.get("success", False)
                    })
                    
                    frame_data = await browser_session.capture_frame_with_metadata()
                    
                    await self._broadcast(session.id, "STEP_COMPLETED", {
                        "session_id": session.id,
                        "feature_name": feature.name,
                        "step_index": step_idx,
                        "step_action": step.action,
                        "success": step_result.get("success", False),
                        "verification": step_result.get("verification"),
                        "frame": frame_data.get("frame") if frame_data.get("success") else None
                    })
                    
                    if not step_result.get("success", False):
                        feature_result["success"] = False
                        
                except Exception as e:
                    feature_result["success"] = False
                    feature_result["steps"].append({
                        "step_id": step.id,
                        "action": step.action,
                        "success": False,
                        "error": str(e)
                    })
                    
                    await self._broadcast(session.id, "STEP_ERROR", {
                        "session_id": session.id,
                        "feature_name": feature.name,
                        "step_index": step_idx,
                        "error": str(e)
                    })
                
                if step_idx < len(feature.steps) - 1:
                    await asyncio.sleep(0.5)
            
            feature_end_time = asyncio.get_event_loop().time()
            
            await self._broadcast(session.id, "FEATURE_COMPLETED", {
                "session_id": session.id,
                "feature_id": feature.id,
                "feature_name": feature.name,
                "feature_index": feature_idx,
                "start_time": feature_start_time,
                "end_time": feature_end_time,
                "duration": feature_end_time - feature_start_time,
                "success": feature_result["success"]
            })
            
            results.append(feature_result)
            
            if feature_idx < len(sorted_features) - 1:
                await asyncio.sleep(1)
        
        session.state = AgentState.FINISHED
        session.finished_at = datetime.utcnow()
        
        await self._update_demo_status(
            session.demo_id,
            DemoStatus.COMPLETED
        )
        
        await self._broadcast(session.id, EventTypes.AGENT_FINISHED, {
            "session_id": session.id,
            "demo_id": session.demo_id,
            "total_features": len(results),
            "successful_features": sum(1 for r in results if r["success"])
        })
        
        return {
            "session_id": session.id,
            "results": results,
            "events": session.events
        }
    
    async def _execute_step_with_verification(
        self,
        browser_session: BrowserSession,
        step: ExecutionStep,
        feature_name: str,
        session_id: str
    ) -> Dict[str, Any]:
        if self._needs_reasoning(step):
            accessibility_tree = await browser_session.get_accessibility_tree()
            resolved = await self._resolve_action(step, accessibility_tree)
            
            tool_name = resolved.get("tool")
            arguments = resolved.get("arguments", {})
            arguments["session_id"] = session_id
            
            try:
                tool_result = await mcp.call_tool(tool_name, arguments)
                result = {"success": True, "output": str(tool_result)}
            except Exception as e:
                result = {"success": False, "error": str(e)}
        else:
            # Simple actions bypass reasoning
            if step.action == "navigate":
                result = await browser_session.navigate(step.value or step.target)
            elif step.action == "wait":
                result = await browser_session.wait(int(step.value) if step.value else 1000)
            else:
                resolved_action = BrowserAction(
                    action=step.action,
                    selector=step.target,
                    value=step.value,
                    wait_ms=500
                )
                result = await browser_session.execute_action(resolved_action)
        
        await browser_session.screenshot(f"{feature_name}_{step.action}")
        
        if self.openai_client and step.success_condition:
            verification = await self._verify_action_with_vision(
                browser_session,
                step,
                result
            )
            result["verification"] = verification
            
            if verification and not verification.get("success", True):
                result["success"] = False
                result["verification_failed"] = True
        
        return result
    
    async def _verify_action_with_vision(
        self,
        browser_session: BrowserSession,
        step: ExecutionStep,
        action_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if not self.openai_client:
            return None
        
        try:
            screenshot_b64 = await browser_session.get_screenshot_base64()
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": VISION_VERIFICATION_PROMPT.format(
                                    action=step.action,
                                    target=step.target or "N/A",
                                    expected=step.success_condition or "Action completed"
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(content[json_start:json_end])
            
        except Exception as e:
            return {"success": True, "error": str(e), "skipped": True}
        
        return None
    
    def _needs_reasoning(self, step: ExecutionStep) -> bool:
        if step.action in ["navigate", "wait", "screenshot"]:
            return False
        
        if step.target and step.target.startswith(("#", ".", "[", "//", "button", "input", "a")):
            return False
        
        return True
    
    async def _resolve_action(
        self,
        step: ExecutionStep,
        accessibility_tree: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self.openai_client and not self.anthropic_client:
            return {
                "tool": "click" if step.action == "click" else "type_text",
                "arguments": {
                    "selector": step.target,
                    "text": step.value
                }
            }
        
        prompt = REASONING_PROMPT.format(
            action=step.action,
            target=step.target or "none",
            value=step.value or "none",
            success_condition=step.success_condition or "action completed",
            accessibility_tree=str(accessibility_tree)[:2000]
        )
        
        try:
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                data = json.loads(response.choices[0].message.content)
            else:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                data = json.loads(content[json_start:json_end])
            
            return data
        except Exception:
            return {
                "tool": "click" if step.action == "click" else "type_text",
                "arguments": {
                    "selector": step.target,
                    "text": step.value
                }
            }
    
    async def _update_demo_status(self, demo_id: str, status: DemoStatus):
        self.supabase.table("demos")\
            .update({"status": status.value, "updated_at": datetime.utcnow().isoformat()})\
            .eq("id", demo_id)\
            .execute()
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        return self._sessions.get(session_id)
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        browser_session = await browser_service.get_session(session.browser_session_id)
        frame = None
        if browser_session:
            frame_data = await browser_session.capture_frame_with_metadata()
            if frame_data.get("success"):
                frame = frame_data.get("frame")
        
        return {
            "session_id": session.id,
            "demo_id": session.demo_id,
            "state": session.state.value,
            "current_feature_index": session.current_feature_index,
            "current_step_index": session.current_step_index,
            "events_count": len(session.events),
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "frame": frame
        }
    
    async def stop_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if session.browser_session_id:
            await browser_service.destroy_session(session.browser_session_id)
        
        session.state = AgentState.FINISHED
        session.finished_at = datetime.utcnow()
        
        if session_id in self._broadcast_callbacks:
            del self._broadcast_callbacks[session_id]
        
        del self._sessions[session_id]
        return True

agent_service = AgentExecutionService()
