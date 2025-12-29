import json
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from ...models.schemas import ExecutionPlan, Feature, ExecutionStep
from ...core.config import settings
from ...core.database import get_supabase

INTENT_SYSTEM_PROMPT = """You are an AI video planning assistant for AutoVidAI. Your job is to analyze user prompts and generate deterministic execution plans for browser automation.

Given a user's prompt about what they want to demonstrate in their app, create a structured execution plan.

Output a JSON object with this structure:
{
  "video_type": "feature_walkthrough" | "onboarding_guide" | "release_highlight",
  "features": [
    {
      "name": "Feature Name",
      "description": "What this feature demonstrates",
      "priority": 1,
      "steps": [
        {
          "action": "navigate" | "click" | "type" | "wait" | "scroll" | "hover" | "screenshot",
          "target": "CSS selector or description",
          "value": "value to type or URL to navigate",
          "reasoning": "Why this step is needed",
          "success_condition": "What indicates success",
          "timeout_ms": 5000
        }
      ]
    }
  ],
  "start_url": "/",
  "estimated_duration_seconds": 60
}

Rules:
1. Be specific with CSS selectors when possible
2. Include wait steps for page loads and animations
3. Order features by priority (1 = highest)
4. Keep steps atomic and verifiable
5. Include screenshot steps at key moments
6. Estimate realistic durations
"""

class IntentService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.supabase = get_supabase()
    
    async def generate_execution_plan(
        self,
        demo_id: str,
        prompt: str,
        app_context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        user_message = self._build_user_message(prompt, app_context)
        
        if self.openai_client:
            plan_data = await self._call_openai(user_message)
        elif self.anthropic_client:
            plan_data = await self._call_anthropic(user_message)
        else:
            plan_data = self._generate_fallback_plan(prompt)
        
        plan = self._parse_plan(demo_id, plan_data)
        
        await self._store_plan(demo_id, plan)
        
        return plan
    
    async def get_plan(self, demo_id: str) -> Optional[ExecutionPlan]:
        result = self.supabase.table("execution_plans")\
            .select("*")\
            .eq("demo_id", demo_id)\
            .single()\
            .execute()
        
        if not result.data:
            return None
        
        return self._row_to_plan(result.data)
    
    def _build_user_message(self, prompt: str, app_context: Optional[Dict[str, Any]]) -> str:
        message = f"User wants to demonstrate: {prompt}\n\n"
        
        if app_context:
            if app_context.get("framework"):
                message += f"Framework: {app_context['framework']}\n"
            if app_context.get("routes"):
                message += f"Available routes: {', '.join(app_context['routes'])}\n"
            if app_context.get("components"):
                message += f"Key components: {', '.join(app_context['components'])}\n"
        
        message += "\nGenerate an execution plan for this demo."
        return message
    
    async def _call_openai(self, user_message: str) -> Dict[str, Any]:
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def _call_anthropic(self, user_message: str) -> Dict[str, Any]:
        response = await self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            system=INTENT_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        content = response.content[0].text
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        return json.loads(content[json_start:json_end])
    
    def _generate_fallback_plan(self, prompt: str) -> Dict[str, Any]:
        return {
            "video_type": "feature_walkthrough",
            "features": [
                {
                    "name": "Main Flow",
                    "description": f"Walkthrough based on: {prompt}",
                    "priority": 1,
                    "steps": [
                        {
                            "action": "navigate",
                            "target": None,
                            "value": "/",
                            "reasoning": "Start at homepage",
                            "success_condition": "Page loaded",
                            "timeout_ms": 5000
                        },
                        {
                            "action": "wait",
                            "target": None,
                            "value": "2000",
                            "reasoning": "Allow page to fully render",
                            "success_condition": "Page stable",
                            "timeout_ms": 3000
                        },
                        {
                            "action": "screenshot",
                            "target": None,
                            "value": "initial_view",
                            "reasoning": "Capture initial state",
                            "success_condition": "Screenshot taken",
                            "timeout_ms": 1000
                        }
                    ]
                }
            ],
            "start_url": "/",
            "estimated_duration_seconds": 30
        }
    
    def _parse_plan(self, demo_id: str, plan_data: Dict[str, Any]) -> ExecutionPlan:
        features = []
        for f_data in plan_data.get("features", []):
            steps = []
            for s_data in f_data.get("steps", []):
                step = ExecutionStep(
                    action=s_data.get("action", "wait"),
                    target=s_data.get("target"),
                    value=s_data.get("value"),
                    reasoning=s_data.get("reasoning"),
                    success_condition=s_data.get("success_condition"),
                    timeout_ms=s_data.get("timeout_ms", 5000)
                )
                steps.append(step)
            
            feature = Feature(
                name=f_data.get("name", "Unnamed Feature"),
                description=f_data.get("description", ""),
                steps=steps,
                priority=f_data.get("priority", 0)
            )
            features.append(feature)
        
        return ExecutionPlan(
            demo_id=demo_id,
            video_type=plan_data.get("video_type", "feature_walkthrough"),
            features=features,
            start_url=plan_data.get("start_url", "/"),
            estimated_duration_seconds=plan_data.get("estimated_duration_seconds", 60),
            metadata={"raw_plan": plan_data}
        )
    
    async def _store_plan(self, demo_id: str, plan: ExecutionPlan):
        plan_dict = {
            "id": plan.id,
            "demo_id": demo_id,
            "video_type": plan.video_type,
            "features": [
                {
                    "id": f.id,
                    "name": f.name,
                    "description": f.description,
                    "priority": f.priority,
                    "steps": [
                        {
                            "id": s.id,
                            "action": s.action,
                            "target": s.target,
                            "value": s.value,
                            "reasoning": s.reasoning,
                            "success_condition": s.success_condition,
                            "timeout_ms": s.timeout_ms
                        }
                        for s in f.steps
                    ]
                }
                for f in plan.features
            ],
            "start_url": plan.start_url,
            "estimated_duration_seconds": plan.estimated_duration_seconds,
            "metadata": plan.metadata
        }
        
        self.supabase.table("execution_plans").upsert(plan_dict).execute()
        
        self.supabase.table("demos")\
            .update({"execution_plan": plan_dict})\
            .eq("id", demo_id)\
            .execute()
    
    def _row_to_plan(self, row: Dict[str, Any]) -> ExecutionPlan:
        features = []
        for f_data in row.get("features", []):
            steps = [
                ExecutionStep(**s_data) for s_data in f_data.get("steps", [])
            ]
            feature = Feature(
                id=f_data.get("id"),
                name=f_data.get("name"),
                description=f_data.get("description"),
                steps=steps,
                priority=f_data.get("priority", 0)
            )
            features.append(feature)
        
        return ExecutionPlan(
            id=row.get("id"),
            demo_id=row.get("demo_id"),
            video_type=row.get("video_type"),
            features=features,
            start_url=row.get("start_url"),
            estimated_duration_seconds=row.get("estimated_duration_seconds"),
            metadata=row.get("metadata", {})
        )

intent_service = IntentService()
