import asyncio
import os
import subprocess
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, field
from ...models.schemas import Clip, RecordingEvent
from ...core.events import event_bus, EventTypes
from ...core.config import settings
from ...core.database import get_supabase

@dataclass
class RecordingSession:
    id: str
    demo_id: str
    status: str = "idle"
    video_path: Optional[str] = None
    events: List[RecordingEvent] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None

class RecorderService:
    def __init__(self):
        self.supabase = get_supabase()
        self._sessions: Dict[str, RecordingSession] = {}
        self._recording_dir = "/tmp/autovid/recordings"
        os.makedirs(self._recording_dir, exist_ok=True)
    
    async def start_recording(self, session_id: str, demo_id: str) -> RecordingSession:
        recording = RecordingSession(
            id=session_id,
            demo_id=demo_id,
            status="recording",
            start_time=asyncio.get_event_loop().time(),
            video_path=f"{self._recording_dir}/{session_id}.webm"
        )
        
        self._sessions[session_id] = recording
        
        await event_bus.publish(
            f"recording:{session_id}",
            EventTypes.RECORDING_STARTED,
            {"session_id": session_id, "demo_id": demo_id}
        )
        
        return recording
    
    async def stop_recording(self, session_id: str) -> Optional[RecordingSession]:
        recording = self._sessions.get(session_id)
        if not recording:
            return None
        
        recording.status = "stopped"
        recording.end_time = asyncio.get_event_loop().time()
        
        await event_bus.publish(
            f"recording:{session_id}",
            EventTypes.RECORDING_STOPPED,
            {"session_id": session_id}
        )
        
        return recording
    
    async def add_event(self, session_id: str, event: RecordingEvent):
        recording = self._sessions.get(session_id)
        if recording:
            recording.events.append(event)
    
    async def add_milestone(
        self,
        session_id: str,
        feature_id: str,
        feature_name: str,
        start_time: float,
        end_time: float
    ):
        recording = self._sessions.get(session_id)
        if recording:
            recording.milestones.append({
                "feature_id": feature_id,
                "feature_name": feature_name,
                "start_time": start_time,
                "end_time": end_time
            })
    
    async def generate_clips(self, session_id: str) -> List[Clip]:
        recording = self._sessions.get(session_id)
        if not recording or not recording.milestones:
            return []
        
        clips = []
        
        for idx, milestone in enumerate(recording.milestones):
            start = milestone["start_time"] - (recording.start_time or 0)
            end = milestone["end_time"] - (recording.start_time or 0)
            duration = end - start
            
            clip_path = f"{self._recording_dir}/{session_id}_clip_{idx}.webm"
            
            if recording.video_path and os.path.exists(recording.video_path):
                await self._extract_clip(
                    recording.video_path,
                    clip_path,
                    start,
                    duration
                )
            
            clip = Clip(
                demo_id=recording.demo_id,
                feature_id=milestone["feature_id"],
                title=milestone["feature_name"],
                start_time=start,
                end_time=end,
                duration=self._format_duration(duration),
                video_url=clip_path if os.path.exists(clip_path) else None,
                order_index=idx
            )
            
            clips.append(clip)
            
            await self._save_clip(clip)
        
        await event_bus.publish(
            f"recording:{session_id}",
            EventTypes.CLIPS_GENERATED,
            {
                "session_id": session_id,
                "demo_id": recording.demo_id,
                "clip_count": len(clips)
            }
        )
        
        return clips
    
    async def _extract_clip(
        self,
        source_path: str,
        output_path: str,
        start_time: float,
        duration: float
    ):
        cmd = [
            "ffmpeg",
            "-y",
            "-i", source_path,
            "-ss", str(start_time),
            "-t", str(duration),
            "-c", "copy",
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
        except Exception as e:
            pass
    
    async def _save_clip(self, clip: Clip):
        clip_dict = {
            "id": clip.id,
            "demo_id": clip.demo_id,
            "title": clip.title,
            "duration": clip.duration,
            "thumbnail_url": clip.thumbnail_url,
            "narration": clip.narration,
            "overlay": clip.overlay,
            "captions": clip.captions,
            "order_index": clip.order_index,
            "created_at": clip.created_at.isoformat()
        }
        
        self.supabase.table("clips").upsert(clip_dict).execute()
    
    def _format_duration(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}:{secs:02d}"
    
    async def get_recording(self, session_id: str) -> Optional[RecordingSession]:
        return self._sessions.get(session_id)

recorder_service = RecorderService()
