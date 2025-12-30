import asyncio
import json
import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from enum import Enum

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    AGENT_ACTION = "AGENT_ACTION"
    AGENT_STEP_STARTED = "AGENT_STEP_STARTED"
    AGENT_STEP_COMPLETED = "AGENT_STEP_COMPLETED"
    AGENT_STEP_FAILED = "AGENT_STEP_FAILED"
    
    FEATURE_MILESTONE = "FEATURE_MILESTONE"
    
    RECORDING_STARTED = "RECORDING_STARTED"
    RECORDING_FRAME = "RECORDING_FRAME"
    RECORDING_READY = "RECORDING_READY"
    RECORDING_FAILED = "RECORDING_FAILED"
    
    CLIPS_GENERATING = "CLIPS_GENERATING"
    CLIPS_GENERATED = "CLIPS_GENERATED"
    CLIP_READY = "CLIP_READY"
    
    EXPORT_STARTED = "EXPORT_STARTED"
    EXPORT_PROGRESS = "EXPORT_PROGRESS"
    EXPORT_COMPLETED = "EXPORT_COMPLETED"
    EXPORT_FAILED = "EXPORT_FAILED"
    
    SANDBOX_CREATING = "SANDBOX_CREATING"
    SANDBOX_READY = "SANDBOX_READY"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    SANDBOX_TERMINATED = "SANDBOX_TERMINATED"
    
    BROWSER_SESSION_CREATED = "BROWSER_SESSION_CREATED"
    BROWSER_SESSION_CLOSED = "BROWSER_SESSION_CLOSED"
    BROWSER_ACTION_COMPLETED = "BROWSER_ACTION_COMPLETED"


class Event:
    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        session_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.id = f"{event_type}_{datetime.utcnow().timestamp()}"
        self.event_type = event_type
        self.data = data
        self.session_id = session_id
        self.project_id = project_id
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "data": self.data,
            "session_id": self.session_id,
            "project_id": self.project_id,
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Event":
        data = json.loads(json_str)
        event = cls(
            event_type=data["event_type"],
            data=data["data"],
            session_id=data.get("session_id"),
            project_id=data.get("project_id"),
        )
        event.id = data["id"]
        event.timestamp = data["timestamp"]
        return event


class EventBus:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._pubsub: Optional[redis.client.PubSub] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self):
        if self._redis is None:
            self._redis = redis.from_url(settings.REDIS_URL)
            self._pubsub = self._redis.pubsub()
            logger.info("Connected to Redis event bus")

    async def disconnect(self):
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        
        logger.info("Disconnected from Redis event bus")

    async def publish(self, event: Event, channel: Optional[str] = None):
        await self.connect()
        
        if channel is None:
            channel = f"events:{event.event_type}"
        
        await self._redis.publish(channel, event.to_json())
        
        for callback in self._subscribers.get(event.event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Event callback error: {e}")

        logger.debug(f"Published event: {event.event_type}")

    async def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

        await self.connect()
        await self._pubsub.subscribe(f"events:{event_type}")
        
        if not self._running:
            self._running = True
            self._listener_task = asyncio.create_task(self._listen())

    async def subscribe_pattern(self, pattern: str, callback: Callable):
        await self.connect()
        await self._pubsub.psubscribe(pattern)
        
        if pattern not in self._subscribers:
            self._subscribers[pattern] = []
        self._subscribers[pattern].append(callback)

        if not self._running:
            self._running = True
            self._listener_task = asyncio.create_task(self._listen())

    async def unsubscribe(self, event_type: str, callback: Callable):
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] if cb != callback
            ]
            if not self._subscribers[event_type]:
                await self._pubsub.unsubscribe(f"events:{event_type}")
                del self._subscribers[event_type]

    async def _listen(self):
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )
                if message and message["type"] in ("message", "pmessage"):
                    event = Event.from_json(message["data"])
                    
                    for callback in self._subscribers.get(event.event_type, []):
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(event)
                            else:
                                callback(event)
                        except Exception as e:
                            logger.error(f"Event handler error: {e}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event listener error: {e}")
                await asyncio.sleep(1)

    async def publish_agent_action(
        self,
        session_id: str,
        action_type: str,
        data: Dict[str, Any],
    ):
        await self.publish(Event(
            event_type=EventType.AGENT_ACTION.value,
            session_id=session_id,
            data={"action_type": action_type, **data},
        ))

    async def publish_milestone(
        self,
        session_id: str,
        milestone_id: str,
        name: str,
        data: Dict[str, Any],
    ):
        await self.publish(Event(
            event_type=EventType.FEATURE_MILESTONE.value,
            session_id=session_id,
            data={"milestone_id": milestone_id, "name": name, **data},
        ))

    async def publish_recording_ready(
        self,
        session_id: str,
        recording_id: str,
        data: Dict[str, Any],
    ):
        await self.publish(Event(
            event_type=EventType.RECORDING_READY.value,
            session_id=session_id,
            data={"recording_id": recording_id, **data},
        ))

    async def publish_clips_generated(
        self,
        session_id: str,
        clips: List[Dict[str, Any]],
    ):
        await self.publish(Event(
            event_type=EventType.CLIPS_GENERATED.value,
            session_id=session_id,
            data={"clips": clips},
        ))

    async def get_recent_events(
        self,
        event_type: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Event]:
        await self.connect()
        
        key = "events:history"
        if event_type:
            key = f"events:history:{event_type}"
        if session_id:
            key = f"events:history:session:{session_id}"

        events_json = await self._redis.lrange(key, 0, limit - 1)
        return [Event.from_json(e) for e in events_json]

    async def store_event(self, event: Event):
        await self.connect()
        
        await self._redis.lpush("events:history", event.to_json())
        await self._redis.ltrim("events:history", 0, 999)
        
        await self._redis.lpush(f"events:history:{event.event_type}", event.to_json())
        await self._redis.ltrim(f"events:history:{event.event_type}", 0, 99)
        
        if event.session_id:
            await self._redis.lpush(f"events:history:session:{event.session_id}", event.to_json())
            await self._redis.ltrim(f"events:history:session:{event.session_id}", 0, 199)


event_bus = EventBus()
