import redis.asyncio as redis
import json
from typing import Any, Callable, Optional
from .config import settings

class EventBus:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None
        
    async def connect(self):
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        
    async def disconnect(self):
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
            
    async def publish(self, channel: str, event_type: str, data: dict):
        if not self._redis:
            return
        message = json.dumps({
            "type": event_type,
            "data": data
        })
        await self._redis.publish(channel, message)
        
    async def subscribe(self, channel: str, callback: Callable):
        if not self._pubsub:
            return
        await self._pubsub.subscribe(channel)
        async for message in self._pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await callback(data)

class EventTypes:
    SANDBOX_CREATED = "SANDBOX_CREATED"
    SANDBOX_READY = "SANDBOX_READY"
    SANDBOX_ERROR = "SANDBOX_ERROR"
    SANDBOX_DESTROYED = "SANDBOX_DESTROYED"
    
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_BUILDING = "PROJECT_BUILDING"
    PROJECT_READY = "PROJECT_READY"
    PROJECT_ERROR = "PROJECT_ERROR"
    
    AGENT_STARTED = "AGENT_STARTED"
    AGENT_ACTION = "AGENT_ACTION"
    AGENT_STEP_COMPLETED = "AGENT_STEP_COMPLETED"
    AGENT_ERROR = "AGENT_ERROR"
    AGENT_FINISHED = "AGENT_FINISHED"
    
    FEATURE_MILESTONE = "FEATURE_MILESTONE"
    
    RECORDING_STARTED = "RECORDING_STARTED"
    RECORDING_FRAME = "RECORDING_FRAME"
    RECORDING_STOPPED = "RECORDING_STOPPED"
    RECORDING_READY = "RECORDING_READY"
    
    CLIPS_GENERATED = "CLIPS_GENERATED"
    EXPORT_STARTED = "EXPORT_STARTED"
    EXPORT_PROGRESS = "EXPORT_PROGRESS"
    EXPORT_COMPLETED = "EXPORT_COMPLETED"

event_bus = EventBus()
