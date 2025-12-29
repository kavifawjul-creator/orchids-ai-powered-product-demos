import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from ..core.events import event_bus

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._streaming_tasks: Dict[str, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
    
    async def broadcast(self, channel: str, message: dict):
        if channel in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[channel]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.add(websocket)
            
            for ws in disconnected:
                self.disconnect(ws, channel)
    
    async def send_to_session(self, session_id: str, message: dict):
        channel = f"session:{session_id}"
        await self.broadcast(channel, message)
    
    def start_frame_streaming(self, session_id: str, browser_session):
        async def stream_task():
            channel = f"session:{session_id}"
            try:
                async for frame_data in browser_session.stream_frames(fps=2):
                    await self.broadcast(channel, frame_data)
            except Exception as e:
                await self.broadcast(channel, {"type": "stream_error", "error": str(e)})
        
        if session_id in self._streaming_tasks:
            self._streaming_tasks[session_id].cancel()
        
        task = asyncio.create_task(stream_task())
        self._streaming_tasks[session_id] = task
    
    def stop_frame_streaming(self, session_id: str):
        if session_id in self._streaming_tasks:
            self._streaming_tasks[session_id].cancel()
            del self._streaming_tasks[session_id]

manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(websocket, channel)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
            elif message.get("type") == "subscribe":
                sub_channel = message.get("channel")
                if sub_channel:
                    await manager.connect(websocket, sub_channel)
            elif message.get("type") == "get_frame":
                session_id = message.get("session_id")
                if session_id:
                    from ..services.browser.service import browser_service
                    screenshot = await browser_service.get_screenshot(session_id)
                    if screenshot:
                        await websocket.send_json({
                            "type": "frame",
                            "frame": screenshot,
                            "session_id": session_id
                        })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception:
        manager.disconnect(websocket, channel)

async def broadcast_event(channel: str, event_type: str, data: dict):
    await manager.broadcast(channel, {
        "type": event_type,
        "data": data
    })

async def broadcast_agent_update(session_id: str, update_type: str, data: dict):
    await manager.send_to_session(session_id, {
        "type": "agent_update",
        "update_type": update_type,
        "data": data
    })

async def broadcast_frame(session_id: str, frame_b64: str, metadata: dict = None):
    await manager.send_to_session(session_id, {
        "type": "frame",
        "frame": frame_b64,
        "metadata": metadata or {}
    })
