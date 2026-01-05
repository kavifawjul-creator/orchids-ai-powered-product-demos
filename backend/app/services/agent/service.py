import asyncio
import logging
import time
import base64
import json
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from openai import AsyncOpenAI

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
    StateVerificationResult,
    RecoveryAction,
)
from app.models.intent import ExecutionPlan, ExecutionStep, StepType
from app.services.browser import browser_service, BrowserAction, BrowserActionType
from app.services.intent import intent_service

logger = logging.getLogger(__name__)

STATE_VERIFICATION_PROMPT = """You are a UI state verification agent. Analyze the current screenshot and determine if the UI is ready for the next action.

NEXT ACTION TO PERFORM:
- Type: {step_type}
- Target: {target}
- Description: {description}
- Expected precondition: {expected_outcome}

Analyze the screenshot and respond with a JSON object:
{{
  "ready": true/false,
  "issue": "Description of any blocking issue (null if ready)",
  "suggestion": "How to resolve the issue (null if ready)",
  "recovery_action": "none" | "close_modal" | "scroll_into_view" | "wait_for_loading" | "click_overlay" | "refresh_page" | "retry",
  "confidence": 0.0-1.0,
  "screenshot_analysis": "Brief description of what you see in the screenshot"
}}

Common issues to check:
1. Modal/dialog blocking the target element
2. Loading spinner or skeleton visible
3. Toast/notification covering content
4. Cookie consent banner blocking
5. Target element not visible (needs scroll)
6. Overlay or backdrop covering the page

If the UI looks ready and the target should be accessible, set ready=true.
Respond ONLY with the JSON object."""


class AgentExecutionService:
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}
        self._plans: Dict[str, ExecutionPlan] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._event_callbacks: List[Callable] = []
        self._pause_events: Dict[str, asyncio.Event] = {}
        self._openai: Optional[AsyncOpenAI] = None

    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai

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

        streaming_task = None
        
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

            # Start live frame streaming
            streaming_task = asyncio.create_task(
                self._stream_frames_to_websocket(session_id, browser_session.id)
            )

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
            # Stop frame streaming
            if streaming_task:
                streaming_task.cancel()
                try:
                    await streaming_task
                except asyncio.CancelledError:
                    pass
            
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

        # Send action overlay to stream manager for live display
        try:
            from ..services.browser.streaming import stream_manager
            await stream_manager.send_action(session.browser_session_id, {
                "action_type": step.step_type.value,
                "action_text": step.description,
                "target": step.target,
                "step_index": step.order,
                "total_steps": session.total_steps
            })
        except Exception as e:
            logger.debug(f"Failed to send action overlay: {e}")

        try:
            screenshot_b64 = None
            if session.config.auto_screenshot:
                screenshot = await browser_service.take_screenshot(session.browser_session_id)
                if screenshot:
                    screenshot_b64 = base64.b64encode(screenshot).decode()
                    if step.screenshot_before:
                        execution.screenshot_before = screenshot_b64

            if screenshot_b64 and session.config.enable_recovery:
                verification = await self.verify_state(session, step, screenshot_b64)
                
                await self._emit_event(AgentEvent(
                    event_type="STATE_VERIFIED",
                    session_id=session.id,
                    data={
                        "step_id": step.id,
                        "ready": verification.ready,
                        "confidence": verification.confidence,
                        "issue": verification.issue,
                        "analysis": verification.screenshot_analysis,
                    },
                ))

                if not verification.ready:
                    logger.warning(f"State verification failed: {verification.issue}")
                    
                    if verification.recovery_action != RecoveryAction.NONE:
                        recovery_success = await self._execute_recovery(session, verification)
                        
                        if recovery_success:
                            await asyncio.sleep(0.5)
                            screenshot = await browser_service.take_screenshot(session.browser_session_id)
                            if screenshot:
                                screenshot_b64 = base64.b64encode(screenshot).decode()
                                re_verify = await self.verify_state(session, step, screenshot_b64)
                                if not re_verify.ready:
                                    raise Exception(f"State not ready after recovery: {re_verify.issue}")
                        else:
                            raise Exception(f"Recovery failed: {verification.issue}")
                    else:
                        raise Exception(f"State not ready: {verification.issue}")

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
            
            # Clear action overlay after step completion
            try:
                from ..services.browser.streaming import stream_manager
                await stream_manager.clear_action(session.browser_session_id)
            except Exception:
                pass
            
            # Broadcast frame after each step for live view
            await self._broadcast_step_frame(session, step)

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

    async def _stream_frames_to_websocket(self, session_id: str, browser_session_id: str):
        """
        Background task that streams live frames to WebSocket clients.
        Runs at ~5 FPS while the agent is executing.
        """
        from ..api.websocket import broadcast_frame
        
        try:
            async for frame_data in browser_service.stream_frames(
                browser_session_id,
                fps=5,
                quality=70
            ):
                if session_id not in self._sessions:
                    break
                    
                session = self._sessions[session_id]
                if session.state in [AgentState.COMPLETED, AgentState.FAILED, AgentState.CANCELLED]:
                    break
                
                # Broadcast frame to all WebSocket subscribers
                await broadcast_frame(
                    session_id=session_id,
                    frame_b64=frame_data["frame"],
                    metadata={
                        "step_index": session.current_step_index,
                        "total_steps": session.total_steps,
                        "state": session.state.value,
                        **frame_data.get("metadata", {})
                    }
                )
        except asyncio.CancelledError:
            logger.debug(f"Frame streaming cancelled for session {session_id}")
        except Exception as e:
            logger.warning(f"Frame streaming error: {e}")

    async def _broadcast_step_frame(self, session: AgentSession, step: ExecutionStep):
        """
        Broadcast a high-quality frame after completing a step.
        This gives clients a clear image at key moments.
        """
        from ..api.websocket import broadcast_agent_update
        
        try:
            # Capture higher quality frame for step completion
            frame = await browser_service.get_live_frame(
                session.browser_session_id,
                quality=85
            )
            
            if frame:
                await broadcast_agent_update(
                    session_id=session.id,
                    update_type="action",
                    data={
                        "action": step.description,
                        "step_index": step.order,
                        "total_steps": session.total_steps,
                        "feature_name": step.metadata.get("feature_name") if step.metadata else None,
                        "frame": frame
                    }
                )
        except Exception as e:
            logger.debug(f"Failed to broadcast step frame: {e}")

    async def verify_state(
        self,
        session: AgentSession,
        step: ExecutionStep,
        screenshot_b64: str,
    ) -> StateVerificationResult:
        if not settings.OPENAI_API_KEY:
            logger.warning("No OpenAI API key, skipping state verification")
            return StateVerificationResult(ready=True, confidence=0.5)

        if step.step_type in [StepType.NARRATE, StepType.WAIT, StepType.SCREENSHOT]:
            return StateVerificationResult(ready=True, confidence=1.0)

        prompt = STATE_VERIFICATION_PROMPT.format(
            step_type=step.step_type.value,
            target=step.target or "N/A",
            description=step.description,
            expected_outcome=step.expected_outcome or "Element should be visible and accessible",
        )

        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_b64}",
                                    "detail": "low",
                                },
                            },
                        ],
                    }
                ],
                max_tokens=512,
            )

            result_text = response.choices[0].message.content
            result_text = result_text.strip()
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]

            result = json.loads(result_text)

            recovery_action = RecoveryAction.NONE
            try:
                recovery_action = RecoveryAction(result.get("recovery_action", "none"))
            except ValueError:
                pass

            return StateVerificationResult(
                ready=result.get("ready", True),
                issue=result.get("issue"),
                suggestion=result.get("suggestion"),
                recovery_action=recovery_action,
                confidence=result.get("confidence", 0.8),
                screenshot_analysis=result.get("screenshot_analysis"),
            )

        except Exception as e:
            logger.error(f"State verification failed: {e}")
            return StateVerificationResult(ready=True, confidence=0.3, issue=str(e))

    async def _execute_recovery(
        self,
        session: AgentSession,
        verification: StateVerificationResult,
    ) -> bool:
        if verification.recovery_action == RecoveryAction.NONE:
            return False

        logger.info(f"Attempting recovery action: {verification.recovery_action.value}")

        await self._emit_event(AgentEvent(
            event_type="RECOVERY_STARTED",
            session_id=session.id,
            data={
                "action": verification.recovery_action.value,
                "issue": verification.issue,
            },
        ))

        success = False

        try:
            if verification.recovery_action == RecoveryAction.CLOSE_MODAL:
                action = BrowserAction(
                    action_type=BrowserActionType.KEYBOARD,
                    value="Escape",
                )
                result = await browser_service.execute_action(session.browser_session_id, action)
                success = result.success
                if not success:
                    close_selectors = [
                        "[aria-label='Close']",
                        "button[class*='close']",
                        "[data-dismiss='modal']",
                        ".modal-close",
                        "button:has(svg[class*='close'])",
                    ]
                    for selector in close_selectors:
                        action = BrowserAction(
                            action_type=BrowserActionType.CLICK,
                            selector=selector,
                        )
                        result = await browser_service.execute_action(session.browser_session_id, action)
                        if result.success:
                            success = True
                            break

            elif verification.recovery_action == RecoveryAction.SCROLL_INTO_VIEW:
                action = BrowserAction(
                    action_type=BrowserActionType.SCROLL,
                    options={"direction": "down", "amount": 300},
                )
                result = await browser_service.execute_action(session.browser_session_id, action)
                success = result.success

            elif verification.recovery_action == RecoveryAction.WAIT_FOR_LOADING:
                await asyncio.sleep(2)
                success = True

            elif verification.recovery_action == RecoveryAction.CLICK_OVERLAY:
                action = BrowserAction(
                    action_type=BrowserActionType.KEYBOARD,
                    value="Escape",
                )
                result = await browser_service.execute_action(session.browser_session_id, action)
                success = result.success

            elif verification.recovery_action == RecoveryAction.REFRESH_PAGE:
                action = BrowserAction(
                    action_type=BrowserActionType.NAVIGATE,
                    options={"refresh": True},
                )
                result = await browser_service.execute_action(session.browser_session_id, action)
                success = result.success
                if success:
                    await asyncio.sleep(1)

            elif verification.recovery_action == RecoveryAction.RETRY:
                await asyncio.sleep(0.5)
                success = True

        except Exception as e:
            logger.error(f"Recovery action failed: {e}")
            success = False

        await self._emit_event(AgentEvent(
            event_type="RECOVERY_COMPLETED",
            session_id=session.id,
            data={
                "action": verification.recovery_action.value,
                "success": success,
            },
        ))

        return success

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
