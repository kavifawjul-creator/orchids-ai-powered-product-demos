import asyncio
import logging
import time
import base64
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from app.core.config import settings
from app.models.agent import (
    AgentState,
    StepStatus,
    AgentEvent,
    StepExecution,
    AgentSessionConfig,
    AgentSession,
    AgentCommand,
    AgentSessionRequest,
    AgentSessionResponse,
)
from app.models.intent import ExecutionPlan, ExecutionStep, StepType
from app.services.browser import browser_service, BrowserAction, BrowserActionType
from app.services.intent import intent_service

logger = logging.getLogger(__name__)


class AgentExecutionService:
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}
        self._plans: Dict[str, ExecutionPlan] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._event_callbacks: List[Callable] = []
        self._pause_events: Dict[str, asyncio.Event] = {}

    def register_event_callback(self, callback: Callable):
        self._event_callbacks.append(callback)

    async def _emit_event(self, event: AgentEvent):
        session = self._sessions.get(event.session_id)
        if session:
            session.events.append(event)

        for callback in self._event_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

    async def create_session(self, request: AgentSessionRequest) -> AgentSessionResponse:
        try:
            plan = await intent_service.get_plan(request.plan_id)
            if not plan:
                return AgentSessionResponse(
                    success=False,
                    error=f"Plan not found: {request.plan_id}",
                )

            config = request.config or AgentSessionConfig()
            session = AgentSession(
                project_id=request.project_id,
                plan_id=request.plan_id,
                config=config,
                total_steps=len(plan.steps),
            )

            for step in plan.steps:
                session.step_executions.append(StepExecution(
                    step_id=step.id,
                    order=step.order,
                ))

            self._sessions[session.id] = session
            self._plans[session.id] = plan
            self._pause_events[session.id] = asyncio.Event()
            self._pause_events[session.id].set()

            await self._emit_event(AgentEvent(
                event_type="SESSION_CREATED",
                session_id=session.id,
                data={"project_id": request.project_id, "plan_id": request.plan_id},
            ))

            if request.auto_start:
                asyncio.create_task(self._start_execution(session.id))

            return AgentSessionResponse(
                success=True,
                session=session,
                message="Agent session created",
            )

        except Exception as e:
            logger.exception(f"Failed to create agent session: {e}")
            return AgentSessionResponse(success=False, error=str(e))

    async def _start_execution(self, session_id: str):
        session = self._sessions.get(session_id)
        if not session:
            return

        plan = self._plans.get(session_id)
        if not plan:
            return

        try:
            session.state = AgentState.INITIALIZING
            session.started_at = datetime.utcnow()

            await self._emit_event(AgentEvent(
                event_type="EXECUTION_STARTED",
                session_id=session_id,
            ))

            browser_session = await browser_service.create_session(
                project_id=session.project_id,
            )
            session.browser_session_id = browser_session.id

            session.state = AgentState.EXECUTING

            for i, step in enumerate(plan.steps):
                if session.state in [AgentState.CANCELLED, AgentState.FAILED]:
                    break

                await self._pause_events[session_id].wait()

                if session.state == AgentState.PAUSED:
                    continue

                session.current_step_index = i
                await self._execute_step(session, step, session.step_executions[i])

                if session.config.pause_between_steps_ms > 0:
                    await asyncio.sleep(session.config.pause_between_steps_ms / 1000)

            if session.state == AgentState.EXECUTING:
                session.state = AgentState.COMPLETED
                session.completed_at = datetime.utcnow()

                await self._emit_event(AgentEvent(
                    event_type="EXECUTION_COMPLETED",
                    session_id=session_id,
                    data={"total_steps": len(plan.steps)},
                ))

        except Exception as e:
            logger.exception(f"Execution failed: {e}")
            session.state = AgentState.FAILED
            session.error = str(e)
            session.completed_at = datetime.utcnow()

            await self._emit_event(AgentEvent(
                event_type="EXECUTION_FAILED",
                session_id=session_id,
                data={"error": str(e)},
            ))

        finally:
            if session.browser_session_id:
                await browser_service.close_session(session.browser_session_id)

    async def _execute_step(
        self,
        session: AgentSession,
        step: ExecutionStep,
        execution: StepExecution,
    ):
        execution.status = StepStatus.RUNNING
        execution.started_at = datetime.utcnow()
        start_time = time.time()

        await self._emit_event(AgentEvent(
            event_type="STEP_STARTED",
            session_id=session.id,
            data={
                "step_id": step.id,
                "order": step.order,
                "description": step.description,
                "step_type": step.step_type.value,
            },
        ))

        try:
            if step.screenshot_before and session.config.auto_screenshot:
                screenshot = await browser_service.take_screenshot(session.browser_session_id)
                if screenshot:
                    execution.screenshot_before = base64.b64encode(screenshot).decode()

            action = self._step_to_browser_action(step)
            if action:
                result = await browser_service.execute_action(session.browser_session_id, action)
                
                if not result.success:
                    raise Exception(result.error or "Action failed")
                
                execution.result = result.result

            if step.wait_after_ms > 0:
                await asyncio.sleep(step.wait_after_ms / 1000)

            if step.screenshot_after and session.config.auto_screenshot:
                screenshot = await browser_service.take_screenshot(session.browser_session_id)
                if screenshot:
                    execution.screenshot_after = base64.b64encode(screenshot).decode()

            execution.status = StepStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int((time.time() - start_time) * 1000)

            await self._emit_event(AgentEvent(
                event_type="STEP_COMPLETED",
                session_id=session.id,
                data={
                    "step_id": step.id,
                    "order": step.order,
                    "duration_ms": execution.duration_ms,
                },
            ))

            await self._check_milestone(session, step.order)

        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            execution.error = str(e)
            execution.duration_ms = int((time.time() - start_time) * 1000)

            if execution.retries < session.config.max_retries_per_step and session.config.enable_recovery:
                execution.retries += 1
                execution.status = StepStatus.RETRYING
                
                await self._emit_event(AgentEvent(
                    event_type="STEP_RETRYING",
                    session_id=session.id,
                    data={"step_id": step.id, "retry": execution.retries},
                ))
                
                await asyncio.sleep(1)
                await self._execute_step(session, step, execution)
            else:
                execution.status = StepStatus.FAILED
                execution.completed_at = datetime.utcnow()

                await self._emit_event(AgentEvent(
                    event_type="STEP_FAILED",
                    session_id=session.id,
                    data={"step_id": step.id, "error": str(e)},
                ))

    def _step_to_browser_action(self, step: ExecutionStep) -> Optional[BrowserAction]:
        mapping = {
            StepType.NAVIGATE: BrowserActionType.NAVIGATE,
            StepType.CLICK: BrowserActionType.CLICK,
            StepType.TYPE: BrowserActionType.TYPE,
            StepType.SCROLL: BrowserActionType.SCROLL,
            StepType.WAIT: BrowserActionType.WAIT,
            StepType.SCREENSHOT: BrowserActionType.SCREENSHOT,
            StepType.HOVER: BrowserActionType.HOVER,
        }

        if step.step_type == StepType.NARRATE:
            return None

        if step.step_type == StepType.ASSERT:
            return None

        action_type = mapping.get(step.step_type)
        if not action_type:
            return None

        return BrowserAction(
            action_type=action_type,
            url=step.target if step.step_type == StepType.NAVIGATE else None,
            selector=step.target if step.step_type != StepType.NAVIGATE else None,
            value=step.value,
            options=step.metadata,
        )

    async def _check_milestone(self, session: AgentSession, step_order: int):
        plan = self._plans.get(session.id)
        if not plan:
            return

        for milestone in plan.milestones:
            if milestone.end_step == step_order:
                await self._emit_event(AgentEvent(
                    event_type="FEATURE_MILESTONE",
                    session_id=session.id,
                    data={
                        "milestone_id": milestone.id,
                        "name": milestone.name,
                        "description": milestone.description,
                        "importance": milestone.importance,
                    },
                ))

    async def handle_command(self, session_id: str, command: AgentCommand, params: Dict[str, Any] = None) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False

        params = params or {}

        if command == AgentCommand.PAUSE:
            session.state = AgentState.PAUSED
            self._pause_events[session_id].clear()
            await self._emit_event(AgentEvent(
                event_type="EXECUTION_PAUSED",
                session_id=session_id,
            ))
            return True

        elif command == AgentCommand.RESUME:
            session.state = AgentState.EXECUTING
            self._pause_events[session_id].set()
            await self._emit_event(AgentEvent(
                event_type="EXECUTION_RESUMED",
                session_id=session_id,
            ))
            return True

        elif command == AgentCommand.STOP:
            session.state = AgentState.CANCELLED
            self._pause_events[session_id].set()
            session.completed_at = datetime.utcnow()
            await self._emit_event(AgentEvent(
                event_type="EXECUTION_CANCELLED",
                session_id=session_id,
            ))
            return True

        elif command == AgentCommand.SKIP_STEP:
            step_index = params.get("step_index", session.current_step_index)
            if 0 <= step_index < len(session.step_executions):
                session.step_executions[step_index].status = StepStatus.SKIPPED
                await self._emit_event(AgentEvent(
                    event_type="STEP_SKIPPED",
                    session_id=session_id,
                    data={"step_index": step_index},
                ))
                return True

        return False

    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        return self._sessions.get(session_id)

    async def get_session_events(self, session_id: str) -> List[AgentEvent]:
        session = self._sessions.get(session_id)
        return session.events if session else []

    async def list_sessions(self, project_id: Optional[str] = None) -> List[AgentSession]:
        sessions = list(self._sessions.values())
        if project_id:
            sessions = [s for s in sessions if s.project_id == project_id]
        return sessions


agent_service = AgentExecutionService()
