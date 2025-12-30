import asyncio
import base64
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.services.browser import browser_service

logger = logging.getLogger(__name__)


class BrowserStreamManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._streaming_tasks: Dict[str, asyncio.Task] = {}
        self._frame_rates: Dict[str, int] = {}
        self._last_frames: Dict[str, bytes] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        
        if session_id not in self._connections:
            self._connections[session_id] = set()
        self._connections[session_id].add(websocket)
        
        logger.info(f"WebSocket connected for session {session_id}")
        
        if session_id not in self._streaming_tasks or self._streaming_tasks[session_id].done():
            self._streaming_tasks[session_id] = asyncio.create_task(
                self._stream_frames(session_id)
            )

    async def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self._connections:
            self._connections[session_id].discard(websocket)
            
            if not self._connections[session_id]:
                del self._connections[session_id]
                
                if session_id in self._streaming_tasks:
                    self._streaming_tasks[session_id].cancel()
                    del self._streaming_tasks[session_id]
        
        logger.info(f"WebSocket disconnected for session {session_id}")

    async def _stream_frames(self, session_id: str):
        frame_interval = 1.0 / self._frame_rates.get(session_id, 10)
        
        while session_id in self._connections and self._connections[session_id]:
            try:
                screenshot = await browser_service.take_screenshot(session_id)
                
                if screenshot:
                    if session_id in self._last_frames and self._last_frames[session_id] == screenshot:
                        await asyncio.sleep(frame_interval)
                        continue
                    
                    self._last_frames[session_id] = screenshot
                    
                    frame_data = {
                        "type": "frame",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": base64.b64encode(screenshot).decode(),
                        "format": "png",
                    }
                    
                    await self._broadcast(session_id, frame_data)
                
                await asyncio.sleep(frame_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Frame streaming error for {session_id}: {e}")
                await asyncio.sleep(1)

    async def _broadcast(self, session_id: str, data: Dict[str, Any]):
        if session_id not in self._connections:
            return
        
        message = json.dumps(data)
        disconnected = set()
        
        for websocket in self._connections[session_id]:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.add(websocket)
        
        for ws in disconnected:
            self._connections[session_id].discard(ws)

    async def send_event(self, session_id: str, event_type: str, data: Dict[str, Any]):
        event = {
            "type": "event",
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }
        await self._broadcast(session_id, event)

    async def send_action(self, session_id: str, action_data: Dict[str, Any]):
        event = {
            "type": "action",
            "timestamp": datetime.utcnow().isoformat(),
            "data": action_data,
        }
        await self._broadcast(session_id, event)

    def set_frame_rate(self, session_id: str, fps: int):
        self._frame_rates[session_id] = max(1, min(fps, 30))

    def get_connection_count(self, session_id: str) -> int:
        return len(self._connections.get(session_id, set()))

    async def handle_websocket(self, session_id: str, websocket: WebSocket):
        await self.connect(session_id, websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "set_fps":
                    self.set_frame_rate(session_id, message.get("fps", 10))
                    
                elif message.get("type") == "request_frame":
                    screenshot = await browser_service.take_screenshot(session_id)
                    if screenshot:
                        await websocket.send_text(json.dumps({
                            "type": "frame",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": base64.b64encode(screenshot).decode(),
                            "format": "png",
                        }))
                        
                elif message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
        except WebSocketDisconnect:
            pass
        except Exception as e:
            logger.error(f"WebSocket error for {session_id}: {e}")
        finally:
            await self.disconnect(session_id, websocket)


stream_manager = BrowserStreamManager()


async def browser_stream_websocket_handler(session_id: str, websocket: WebSocket):
    await stream_manager.handle_websocket(session_id, websocket)
