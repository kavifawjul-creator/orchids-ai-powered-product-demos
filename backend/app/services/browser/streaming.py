import asyncio
import base64
import json
import logging
import hashlib
from typing import Dict, Set, Optional, Any, Literal
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.services.browser import browser_service

logger = logging.getLogger(__name__)


# Quality presets for streaming
QUALITY_PRESETS: Dict[str, Dict[str, Any]] = {
    "low": {"fps": 5, "jpeg_quality": 50, "description": "Low bandwidth mode"},
    "medium": {"fps": 10, "jpeg_quality": 70, "description": "Balanced quality/performance"},
    "high": {"fps": 15, "jpeg_quality": 85, "description": "High quality streaming"},
}

StreamQuality = Literal["low", "medium", "high"]


class BrowserStreamManager:
    """
    Enhanced browser streaming manager with JPEG compression,
    quality presets, action overlays, and efficient delta-frame detection.
    """
    
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._streaming_tasks: Dict[str, asyncio.Task] = {}
        self._quality_settings: Dict[str, str] = {}  # session_id -> quality preset name
        self._last_frame_hashes: Dict[str, str] = {}  # For efficient delta detection
        self._current_actions: Dict[str, Dict[str, Any]] = {}  # Current action overlay data
        self._connection_stats: Dict[str, Dict[str, Any]] = {}  # Connection statistics

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        
        if session_id not in self._connections:
            self._connections[session_id] = set()
            self._connection_stats[session_id] = {
                "frames_sent": 0,
                "frames_skipped": 0,
                "connected_at": datetime.utcnow().isoformat(),
                "bytes_sent": 0
            }
        self._connections[session_id].add(websocket)
        
        logger.info(f"WebSocket connected for session {session_id} (total: {len(self._connections[session_id])})")
        
        # Send initial connection acknowledgment with quality options
        await websocket.send_text(json.dumps({
            "type": "connected",
            "session_id": session_id,
            "quality_presets": QUALITY_PRESETS,
            "current_quality": self._quality_settings.get(session_id, "medium")
        }))
        
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
                
                # Cleanup session data
                self._last_frame_hashes.pop(session_id, None)
                self._current_actions.pop(session_id, None)
                self._connection_stats.pop(session_id, None)
                self._quality_settings.pop(session_id, None)
        
        logger.info(f"WebSocket disconnected for session {session_id}")

    def set_quality(self, session_id: str, quality: StreamQuality):
        """Set streaming quality preset for a session."""
        if quality in QUALITY_PRESETS:
            self._quality_settings[session_id] = quality
            logger.info(f"Quality set to {quality} for session {session_id}")

    def get_quality_settings(self, session_id: str) -> Dict[str, Any]:
        """Get current quality settings for a session."""
        preset_name = self._quality_settings.get(session_id, "medium")
        return QUALITY_PRESETS.get(preset_name, QUALITY_PRESETS["medium"])

    def set_current_action(self, session_id: str, action_data: Optional[Dict[str, Any]]):
        """Set the current action being performed for overlay display."""
        if action_data:
            self._current_actions[session_id] = {
                **action_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            self._current_actions.pop(session_id, None)

    async def _stream_frames(self, session_id: str):
        """Stream frames with JPEG compression and delta detection."""
        
        while session_id in self._connections and self._connections[session_id]:
            try:
                settings = self.get_quality_settings(session_id)
                fps = settings["fps"]
                quality = settings["jpeg_quality"]
                frame_interval = 1.0 / fps
                
                # Use the optimized JPEG screenshot from browser_service
                frame_b64 = await browser_service.get_live_frame(session_id, quality=quality)
                
                if frame_b64:
                    # Efficient delta detection using hash
                    frame_hash = hashlib.md5(frame_b64.encode()[:1000]).hexdigest()
                    
                    if session_id in self._last_frame_hashes and self._last_frame_hashes[session_id] == frame_hash:
                        # Frame unchanged, skip sending
                        if session_id in self._connection_stats:
                            self._connection_stats[session_id]["frames_skipped"] += 1
                        await asyncio.sleep(frame_interval)
                        continue
                    
                    self._last_frame_hashes[session_id] = frame_hash
                    
                    # Build frame data with action overlay
                    frame_data = {
                        "type": "frame",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": frame_b64,
                        "format": "jpeg",
                        "quality": quality,
                    }
                    
                    # Add action overlay if present
                    if session_id in self._current_actions:
                        frame_data["action_overlay"] = self._current_actions[session_id]
                    
                    await self._broadcast(session_id, frame_data)
                    
                    # Update stats
                    if session_id in self._connection_stats:
                        self._connection_stats[session_id]["frames_sent"] += 1
                        self._connection_stats[session_id]["bytes_sent"] += len(frame_b64)
                
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
        """Send action event and update overlay."""
        self.set_current_action(session_id, action_data)
        event = {
            "type": "action",
            "timestamp": datetime.utcnow().isoformat(),
            "data": action_data,
        }
        await self._broadcast(session_id, event)

    async def clear_action(self, session_id: str):
        """Clear the current action overlay."""
        self.set_current_action(session_id, None)
        await self._broadcast(session_id, {
            "type": "action_cleared",
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_connection_count(self, session_id: str) -> int:
        return len(self._connections.get(session_id, set()))

    def get_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get streaming statistics for a session."""
        return self._connection_stats.get(session_id)

    async def handle_websocket(self, session_id: str, websocket: WebSocket):
        await self.connect(session_id, websocket)
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "set_quality":
                    quality = message.get("quality", "medium")
                    if quality in QUALITY_PRESETS:
                        self.set_quality(session_id, quality)
                        await websocket.send_text(json.dumps({
                            "type": "quality_changed",
                            "quality": quality,
                            "settings": QUALITY_PRESETS[quality]
                        }))
                
                elif msg_type == "set_fps":
                    # Legacy support - map to quality preset
                    fps = message.get("fps", 10)
                    if fps <= 5:
                        self.set_quality(session_id, "low")
                    elif fps <= 10:
                        self.set_quality(session_id, "medium")
                    else:
                        self.set_quality(session_id, "high")
                    
                elif msg_type == "request_frame":
                    settings = self.get_quality_settings(session_id)
                    frame_b64 = await browser_service.get_live_frame(
                        session_id, 
                        quality=settings["jpeg_quality"]
                    )
                    if frame_b64:
                        await websocket.send_text(json.dumps({
                            "type": "frame",
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": frame_b64,
                            "format": "jpeg",
                            "quality": settings["jpeg_quality"],
                            "action_overlay": self._current_actions.get(session_id)
                        }))
                
                elif msg_type == "get_stats":
                    stats = self.get_stats(session_id)
                    await websocket.send_text(json.dumps({
                        "type": "stats",
                        "data": stats
                    }))
                        
                elif msg_type == "ping":
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
