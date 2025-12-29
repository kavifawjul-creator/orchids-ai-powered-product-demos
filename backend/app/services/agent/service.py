import asyncio
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
from ..intent.service import intent_service

REASONING_PROMPT = """You are an AI agent executing a browser automation step.

Current step to execute:
- Action: {action}
- Target: {target}
- Value: {value}
- Expected: {success_condition}

Page accessibility snapshot:
{accessibility_tree}

Based on the page state, provide the exact CSS selector or action parameters to execute this step.
If the target is a description, find the best matching element.

Output JSON:
{{
  "selector": "exact CSS selector",
  "action": "click|type|navigate|scroll|wait",
  "value": "value if needed",
  "reasoning": "why this action"
}}
"""

class AgentExecutionService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.supabase = get_supabase()
        self._sessions: Dict[str, AgentSession] = {}
    
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
        
        await event_bus.publish(
            f"agent:{session.id}",
            EventTypes.AGENT_STARTED,
            {"session_id": session.id, "demo_id": demo_id}
        )
        
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
            
            await event_bus.publish(
                f"agent:{session.id}",
                EventTypes.AGENT_ACTION,
                {
                    "session_id": session.id,
                    "type": "feature_start",
                    "feature": feature.name,
                    "feature_index": feature_idx
                }
            )
            
            feature_result = {
                "feature_id": feature.id,
                "feature_name": feature.name,
                "steps": [],
                "success": True
            }
            
            for step_idx, step in enumerate(feature.steps):
                session.current_step_index = step_idx
                
                try:
                    step_result = await self._execute_step(
                        browser_session,
                        step,
                        feature.name
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
                    
                    await event_bus.publish(
                        f"agent:{session.id}",
                        EventTypes.AGENT_STEP_COMPLETED,
                        {
                            "session_id": session.id,
                            "feature": feature.name,
                            "step_index": step_idx,
                            "step_action": step.action,
                            "success": step_result.get("success", False)
                        }
                    )
                    
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
                    
                    await event_bus.publish(
                        f"agent:{session.id}",
                        EventTypes.AGENT_ERROR,
                        {
                            "session_id": session.id,
                            "feature": feature.name,
                            "step_index": step_idx,
                            "error": str(e)
                        }
                    )
                
                if step_idx < len(feature.steps) - 1:
                    await asyncio.sleep(0.5)
            
            feature_end_time = asyncio.get_event_loop().time()
            
            await event_bus.publish(
                f"agent:{session.id}",
                EventTypes.FEATURE_MILESTONE,
                {
                    "session_id": session.id,
                    "feature_id": feature.id,
                    "feature_name": feature.name,
                    "start_time": feature_start_time,
                    "end_time": feature_end_time,
                    "success": feature_result["success"]
                }
            )
            
            results.append(feature_result)
            
            if feature_idx < len(sorted_features) - 1:
                await asyncio.sleep(1)
        
        session.state = AgentState.FINISHED
        session.finished_at = datetime.utcnow()
        
        await self._update_demo_status(
            session.demo_id,
            DemoStatus.COMPLETED
        )
        
        await event_bus.publish(
            f"agent:{session.id}",
            EventTypes.AGENT_FINISHED,
            {
                "session_id": session.id,
                "demo_id": session.demo_id,
                "results": results
            }
        )
        
        return {
            "session_id": session.id,
            "results": results,
            "events": session.events
        }
    
    async def _execute_step(
        self,
        browser_session: BrowserSession,
        step: ExecutionStep,
        feature_name: str
    ) -> Dict[str, Any]:
        if self._needs_reasoning(step):
            accessibility_tree = await browser_session.get_accessibility_tree()
            resolved_action = await self._resolve_action(step, accessibility_tree)
        else:
            resolved_action = BrowserAction(
                action=step.action,
                selector=step.target,
                value=step.value,
                wait_ms=500
            )
        
        result = await browser_session.execute_action(resolved_action)
        
        await browser_session.screenshot(f"{feature_name}_{step.action}")
        
        return result
    
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
    ) -> BrowserAction:
        if not self.openai_client and not self.anthropic_client:
            return BrowserAction(
                action=step.action,
                selector=step.target,
                value=step.value,
                wait_ms=500
            )
        
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
                import json
                data = json.loads(response.choices[0].message.content)
            else:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                import json
                content = response.content[0].text
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                data = json.loads(content[json_start:json_end])
            
            return BrowserAction(
                action=data.get("action", step.action),
                selector=data.get("selector", step.target),
                value=data.get("value", step.value),
                wait_ms=500
            )
        except Exception:
            return BrowserAction(
                action=step.action,
                selector=step.target,
                value=step.value,
                wait_ms=500
            )
    
    async def _update_demo_status(self, demo_id: str, status: DemoStatus):
        self.supabase.table("demos")\
            .update({"status": status.value, "updated_at": datetime.utcnow().isoformat()})\
            .eq("id", demo_id)\
            .execute()
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        return self._sessions.get(session_id)
    
    async def stop_session(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False
        
        if session.browser_session_id:
            await browser_service.destroy_session(session.browser_session_id)
        
        session.state = AgentState.FINISHED
        session.finished_at = datetime.utcnow()
        
        del self._sessions[session_id]
        return True

agent_service = AgentExecutionService()
