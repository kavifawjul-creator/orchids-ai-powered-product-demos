import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from supabase import create_client, Client

from app.core.config import settings
from app.models.intent import (
    IntentType,
    StepType,
    ExecutionStep,
    FeatureMilestone,
    ExecutionPlan,
    IntentAnalysis,
    PlanGenerationRequest,
    PlanGenerationResponse,
)
from app.services.browser import MCP_BROWSER_TOOLS

logger = logging.getLogger(__name__)


INTENT_ANALYSIS_PROMPT = """You are an AI that analyzes user requests to understand their intent for creating product demo videos.

Given the user's request and application context, analyze their intent and provide structured output.

User Request: {user_prompt}

Application Context:
- URL: {app_url}
- Additional Context: {app_context}

Analyze the intent and respond with a JSON object containing:
{{
  "intent_type": "explore" | "demonstrate_feature" | "walkthrough" | "compare" | "onboarding" | "custom",
  "confidence": 0.0-1.0,
  "features_to_showcase": ["list of features to demonstrate"],
  "suggested_routes": ["list of URL routes or pages to visit"],
  "key_interactions": ["list of key user interactions to perform"],
  "target_audience": "description of target audience",
  "tone": "professional" | "casual" | "technical" | "friendly",
  "estimated_steps": number
}}

Respond ONLY with the JSON object, no additional text."""


PLAN_GENERATION_PROMPT = """You are an AI that generates detailed execution plans for browser automation to create product demo videos.

Given the intent analysis and application context, create a step-by-step execution plan.

Intent Analysis:
{intent_analysis}

User Request: {user_prompt}

Application:
- URL: {app_url}
- Context: {app_context}

Available browser actions:
{browser_tools}

Generate a detailed execution plan as a JSON object:
{{
  "title": "Demo title",
  "description": "Brief description of the demo",
  "steps": [
    {{
      "order": 1,
      "step_type": "navigate" | "click" | "type" | "scroll" | "wait" | "screenshot" | "hover" | "assert" | "narrate",
      "description": "Human-readable description of this step",
      "target": "CSS selector or URL (if applicable)",
      "value": "Text to type or value (if applicable)",
      "wait_after_ms": 500,
      "screenshot_before": false,
      "screenshot_after": true,
      "narration": "Voiceover text for this step (if include_narration is true)",
      "expected_outcome": "What should happen after this step"
    }}
  ],
  "milestones": [
    {{
      "name": "Feature milestone name",
      "description": "What this milestone demonstrates",
      "start_step": 1,
      "end_step": 5,
      "importance": "high" | "medium" | "low"
    }}
  ],
  "estimated_duration_seconds": 60
}}

Guidelines:
1. Start with navigating to the app URL
2. Include natural pauses and scroll actions for realistic demos
3. Group related steps into milestones
4. Include narration text that explains what's happening
5. Use specific CSS selectors when targeting elements
6. Maximum {max_steps} steps allowed
7. Make the demo engaging and highlight key features

Respond ONLY with the JSON object, no additional text."""


class IntentPlanningService:
    def __init__(self):
        self._openai: Optional[AsyncOpenAI] = None
        self._anthropic: Optional[AsyncAnthropic] = None
        self._supabase: Optional[Client] = None

    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

    @property
    def anthropic(self) -> AsyncAnthropic:
        if self._anthropic is None:
            self._anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._anthropic

    @property
    def supabase(self) -> Client:
        if self._supabase is None:
            self._supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return self._supabase

    async def analyze_intent(
        self,
        user_prompt: str,
        app_url: str,
        app_context: Optional[Dict[str, Any]] = None,
    ) -> IntentAnalysis:
        prompt = INTENT_ANALYSIS_PROMPT.format(
            user_prompt=user_prompt,
            app_url=app_url,
            app_context=json.dumps(app_context or {}),
        )

        try:
            if settings.ANTHROPIC_API_KEY:
                response = await self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.content[0].text
            elif settings.OPENAI_API_KEY:
                response = await self.openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                )
                result_text = response.choices[0].message.content
            else:
                return self._default_intent_analysis(user_prompt)

            result = json.loads(result_text)
            return IntentAnalysis(
                intent_type=IntentType(result.get("intent_type", "walkthrough")),
                confidence=result.get("confidence", 0.8),
                features_to_showcase=result.get("features_to_showcase", []),
                suggested_routes=result.get("suggested_routes", []),
                key_interactions=result.get("key_interactions", []),
                target_audience=result.get("target_audience", "general"),
                tone=result.get("tone", "professional"),
                estimated_steps=result.get("estimated_steps", 10),
            )

        except Exception as e:
            logger.error(f"Intent analysis failed: {e}")
            return self._default_intent_analysis(user_prompt)

    def _default_intent_analysis(self, user_prompt: str) -> IntentAnalysis:
        return IntentAnalysis(
            intent_type=IntentType.WALKTHROUGH,
            confidence=0.5,
            features_to_showcase=["main features"],
            suggested_routes=["/"],
            key_interactions=["click", "navigate"],
            target_audience="general",
            tone="professional",
            estimated_steps=10,
        )

    async def generate_plan(self, request: PlanGenerationRequest) -> PlanGenerationResponse:
        try:
            intent_analysis = await self.analyze_intent(
                user_prompt=request.user_prompt,
                app_url=request.app_url,
                app_context=request.app_context,
            )

            browser_tools_str = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in MCP_BROWSER_TOOLS
            ])

            prompt = PLAN_GENERATION_PROMPT.format(
                intent_analysis=intent_analysis.model_dump_json(),
                user_prompt=request.user_prompt,
                app_url=request.app_url,
                app_context=json.dumps(request.app_context or {}),
                browser_tools=browser_tools_str,
                max_steps=request.max_steps,
            )

            if settings.ANTHROPIC_API_KEY:
                response = await self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                )
                result_text = response.content[0].text
            elif settings.OPENAI_API_KEY:
                response = await self.openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                )
                result_text = response.choices[0].message.content
            else:
                return PlanGenerationResponse(
                    success=False,
                    error="No LLM API key configured",
                )

            result = json.loads(result_text)

            steps = []
            for step_data in result.get("steps", []):
                steps.append(ExecutionStep(
                    order=step_data.get("order", len(steps) + 1),
                    step_type=StepType(step_data.get("step_type", "click")),
                    description=step_data.get("description", ""),
                    target=step_data.get("target"),
                    value=step_data.get("value"),
                    wait_after_ms=step_data.get("wait_after_ms", 500),
                    screenshot_before=step_data.get("screenshot_before", False),
                    screenshot_after=step_data.get("screenshot_after", True),
                    narration=step_data.get("narration") if request.include_narration else None,
                    expected_outcome=step_data.get("expected_outcome"),
                ))

            milestones = []
            for ms_data in result.get("milestones", []):
                milestone_steps = [s for s in steps if ms_data.get("start_step", 0) <= s.order <= ms_data.get("end_step", 0)]
                milestones.append(FeatureMilestone(
                    name=ms_data.get("name", ""),
                    description=ms_data.get("description", ""),
                    steps=milestone_steps,
                    start_step=ms_data.get("start_step", 1),
                    end_step=ms_data.get("end_step", len(steps)),
                    importance=ms_data.get("importance", "medium"),
                ))

            plan = ExecutionPlan(
                project_id=request.project_id,
                intent_type=intent_analysis.intent_type,
                user_prompt=request.user_prompt,
                title=result.get("title", "Product Demo"),
                description=result.get("description", ""),
                steps=steps,
                milestones=milestones,
                estimated_duration_seconds=result.get("estimated_duration_seconds", 60),
                metadata={
                    "app_url": request.app_url,
                    "demo_style": request.demo_style,
                },
            )

            await self._store_plan(plan)

            return PlanGenerationResponse(
                success=True,
                plan=plan,
                intent_analysis=intent_analysis,
            )

        except Exception as e:
            logger.exception(f"Plan generation failed: {e}")
            return PlanGenerationResponse(
                success=False,
                error=str(e),
            )

    async def _store_plan(self, plan: ExecutionPlan):
        try:
            plan_data = {
                "id": plan.id,
                "project_id": plan.project_id,
                "demo_id": plan.demo_id,
                "intent_type": plan.intent_type.value,
                "user_prompt": plan.user_prompt,
                "title": plan.title,
                "description": plan.description,
                "steps": json.dumps([s.model_dump() for s in plan.steps]),
                "milestones": json.dumps([m.model_dump() for m in plan.milestones]),
                "estimated_duration_seconds": plan.estimated_duration_seconds,
                "metadata": json.dumps(plan.metadata),
            }
            self.supabase.table("execution_plans").insert(plan_data).execute()
            logger.info(f"Stored execution plan: {plan.id}")
        except Exception as e:
            logger.error(f"Failed to store plan: {e}")

    async def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        try:
            result = self.supabase.table("execution_plans").select("*").eq("id", plan_id).execute()
            if not result.data:
                return None

            row = result.data[0]
            steps = [ExecutionStep(**s) for s in json.loads(row["steps"])]
            milestones = [FeatureMilestone(**m) for m in json.loads(row["milestones"])]

            return ExecutionPlan(
                id=row["id"],
                project_id=row["project_id"],
                demo_id=row.get("demo_id"),
                intent_type=IntentType(row["intent_type"]),
                user_prompt=row["user_prompt"],
                title=row["title"],
                description=row["description"],
                steps=steps,
                milestones=milestones,
                estimated_duration_seconds=row["estimated_duration_seconds"],
                metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
                created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")) if row.get("created_at") else datetime.utcnow(),
            )
        except Exception as e:
            logger.error(f"Failed to get plan {plan_id}: {e}")
            return None

    async def list_plans(self, project_id: str) -> List[ExecutionPlan]:
        try:
            result = self.supabase.table("execution_plans").select("*").eq("project_id", project_id).order("created_at", desc=True).execute()
            plans = []
            for row in result.data:
                steps = [ExecutionStep(**s) for s in json.loads(row["steps"])]
                milestones = [FeatureMilestone(**m) for m in json.loads(row["milestones"])]
                plans.append(ExecutionPlan(
                    id=row["id"],
                    project_id=row["project_id"],
                    demo_id=row.get("demo_id"),
                    intent_type=IntentType(row["intent_type"]),
                    user_prompt=row["user_prompt"],
                    title=row["title"],
                    description=row["description"],
                    steps=steps,
                    milestones=milestones,
                    estimated_duration_seconds=row["estimated_duration_seconds"],
                    metadata=json.loads(row["metadata"]) if row.get("metadata") else {},
                ))
            return plans
        except Exception as e:
            logger.error(f"Failed to list plans: {e}")
            return []


intent_service = IntentPlanningService()
