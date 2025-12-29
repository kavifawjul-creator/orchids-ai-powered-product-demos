import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from ..core.events import event_bus

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
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
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception:
        manager.disconnect(websocket, channel)

async def broadcast_event(channel: str, event_type: str, data: dict):
    await manager.broadcast(channel, {
        "type": event_type,
        "data": data
    })
