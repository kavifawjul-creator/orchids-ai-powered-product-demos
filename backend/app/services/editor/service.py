"""
Editor Service

Provides video editing operations including:
- Clip trimming (set start/end points)
- Clip splitting
- TTS narration generation
- Text overlay management
"""

import os
import asyncio
import logging
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_supabase
from app.services.audio.service import audio_service
from app.services.storage.service import storage_service

logger = logging.getLogger(__name__)


class TrimClipRequest(BaseModel):
    """Request to trim a clip to new start/end points."""
    trim_start: float = Field(ge=0, description="Start time in seconds")
    trim_end: Optional[float] = Field(None, description="End time in seconds (null = end of clip)")


class SplitClipRequest(BaseModel):
    """Request to split a clip at a specific point."""
    split_point: float = Field(gt=0, description="Time in seconds where to split")


class GenerateNarrationRequest(BaseModel):
    """Request to generate TTS narration for a clip."""
    text: str = Field(..., min_length=1, max_length=1000)
    voice: str = Field(default="nova", pattern="^(alloy|echo|fable|onyx|nova|shimmer)$")
    speed: float = Field(default=1.0, ge=0.25, le=4.0)


class TextOverlay(BaseModel):
    """Text overlay configuration for a clip."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str = Field(..., min_length=1, max_length=200)
    position_x: float = Field(default=50, ge=0, le=100, description="X position as percentage")
    position_y: float = Field(default=90, ge=0, le=100, description="Y position as percentage")
    font_size: int = Field(default=24, ge=12, le=72)
    font_color: str = Field(default="#ffffff")
    background_color: str = Field(default="rgba(0,0,0,0.5)")
    animation: str = Field(default="fade", pattern="^(none|fade|slide_up|slide_down)$")
    start_time: float = Field(default=0, ge=0)
    end_time: Optional[float] = Field(None, description="End time (null = end of clip)")


class ClipTrimResult(BaseModel):
    """Result of a clip trim operation."""
    success: bool
    clip_id: str
    trim_start: float
    trim_end: Optional[float]
    new_duration: Optional[float] = None
    error: Optional[str] = None


class ClipSplitResult(BaseModel):
    """Result of a clip split operation."""
    success: bool
    original_clip_id: str
    first_clip_id: Optional[str] = None
    second_clip_id: Optional[str] = None
    error: Optional[str] = None


class NarrationResult(BaseModel):
    """Result of narration generation."""
    success: bool
    clip_id: str
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    voice: Optional[str] = None
    error: Optional[str] = None


class EditorService:
    """
    Service for video editor operations.
    Handles clip trimming, splitting, narration generation, and overlays.
    """
    
    def __init__(self):
        self.supabase = get_supabase()
        self.output_dir = "/tmp/autovid/editor"
        os.makedirs(self.output_dir, exist_ok=True)

    async def trim_clip(self, clip_id: str, request: TrimClipRequest) -> ClipTrimResult:
        """
        Set trim points for a clip without actually cutting the video.
        The trim will be applied during export.
        """
        try:
            # Get clip from database
            result = self.supabase.table("clips").select("*").eq("id", clip_id).single().execute()
            if not result.data:
                return ClipTrimResult(
                    success=False,
                    clip_id=clip_id,
                    trim_start=request.trim_start,
                    trim_end=request.trim_end,
                    error="Clip not found"
                )
            
            clip = result.data
            original_duration = clip.get("duration", 0)
            
            # Validate trim points
            if request.trim_end:
                if request.trim_end <= request.trim_start:
                    return ClipTrimResult(
                        success=False,
                        clip_id=clip_id,
                        trim_start=request.trim_start,
                        trim_end=request.trim_end,
                        error="End time must be greater than start time"
                    )
                if isinstance(original_duration, (int, float)) and request.trim_end > original_duration:
                    return ClipTrimResult(
                        success=False,
                        clip_id=clip_id,
                        trim_start=request.trim_start,
                        trim_end=request.trim_end,
                        error=f"End time exceeds clip duration ({original_duration}s)"
                    )
            
            # Calculate new duration
            end_time = request.trim_end if request.trim_end else original_duration
            new_duration = end_time - request.trim_start if isinstance(end_time, (int, float)) else None
            
            # Update clip in database
            update_data = {
                "trim_start": request.trim_start,
                "trim_end": request.trim_end,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("clips").update(update_data).eq("id", clip_id).execute()
            
            logger.info(f"Clip {clip_id} trimmed: {request.trim_start}s - {request.trim_end or 'end'}s")
            
            return ClipTrimResult(
                success=True,
                clip_id=clip_id,
                trim_start=request.trim_start,
                trim_end=request.trim_end,
                new_duration=new_duration
            )
            
        except Exception as e:
            logger.error(f"Failed to trim clip {clip_id}: {e}")
            return ClipTrimResult(
                success=False,
                clip_id=clip_id,
                trim_start=request.trim_start,
                trim_end=request.trim_end,
                error=str(e)
            )

    async def split_clip(self, clip_id: str, request: SplitClipRequest) -> ClipSplitResult:
        """
        Split a clip at a specific point, creating two new clips.
        The original clip becomes the first part.
        """
        try:
            # Get clip from database
            result = self.supabase.table("clips").select("*").eq("id", clip_id).single().execute()
            if not result.data:
                return ClipSplitResult(
                    success=False,
                    original_clip_id=clip_id,
                    error="Clip not found"
                )
            
            clip = result.data
            demo_id = clip["demo_id"]
            order_index = clip.get("order_index", 0)
            
            # Validate split point
            original_duration = clip.get("duration", 0)
            if isinstance(original_duration, str):
                # Parse duration string like "00:05"
                try:
                    parts = original_duration.split(":")
                    original_duration = int(parts[0]) * 60 + int(parts[1])
                except:
                    original_duration = 30  # Default
            
            if request.split_point >= original_duration:
                return ClipSplitResult(
                    success=False,
                    original_clip_id=clip_id,
                    error=f"Split point ({request.split_point}s) exceeds clip duration ({original_duration}s)"
                )
            
            # Create second clip (new)
            second_clip_id = str(uuid.uuid4())
            second_clip_data = {
                "id": second_clip_id,
                "demo_id": demo_id,
                "feature_id": clip.get("feature_id", ""),
                "title": f"{clip.get('title', 'Clip')} (Part 2)",
                "start_time": clip.get("start_time", 0) + request.split_point,
                "end_time": clip.get("end_time"),
                "duration": f"{int((original_duration - request.split_point) // 60):02d}:{int((original_duration - request.split_point) % 60):02d}",
                "video_url": clip.get("video_url"),  # Same source, different trim
                "trim_start": request.split_point,
                "trim_end": None,
                "narration": None,  # Clear narration for second part
                "order_index": order_index + 1,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Update original clip to end at split point
            first_clip_updates = {
                "title": f"{clip.get('title', 'Clip')} (Part 1)",
                "trim_end": request.split_point,
                "duration": f"{int(request.split_point // 60):02d}:{int(request.split_point % 60):02d}",
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Increment order_index for all clips after the split
            self.supabase.table("clips")\
                .update({"order_index": order_index + 2})\
                .eq("demo_id", demo_id)\
                .gt("order_index", order_index)\
                .execute()
            
            # Insert second clip
            self.supabase.table("clips").insert(second_clip_data).execute()
            
            # Update first clip
            self.supabase.table("clips").update(first_clip_updates).eq("id", clip_id).execute()
            
            logger.info(f"Clip {clip_id} split at {request.split_point}s -> {clip_id}, {second_clip_id}")
            
            return ClipSplitResult(
                success=True,
                original_clip_id=clip_id,
                first_clip_id=clip_id,
                second_clip_id=second_clip_id
            )
            
        except Exception as e:
            logger.error(f"Failed to split clip {clip_id}: {e}")
            return ClipSplitResult(
                success=False,
                original_clip_id=clip_id,
                error=str(e)
            )

    async def generate_narration(
        self, 
        clip_id: str, 
        request: GenerateNarrationRequest
    ) -> NarrationResult:
        """
        Generate TTS audio for a clip's narration.
        Uses OpenAI TTS API via audio_service.
        """
        try:
            # Get clip from database
            result = self.supabase.table("clips").select("*").eq("id", clip_id).single().execute()
            if not result.data:
                return NarrationResult(
                    success=False,
                    clip_id=clip_id,
                    error="Clip not found"
                )
            
            clip = result.data
            demo_id = clip["demo_id"]
            
            # Generate audio using TTS
            audio_filename = f"{demo_id}_{clip_id}_narration.mp3"
            audio_path = await audio_service.generate_narration_with_options(
                text=request.text,
                output_filename=audio_filename,
                voice=request.voice,
                speed=request.speed
            )
            
            if not audio_path:
                return NarrationResult(
                    success=False,
                    clip_id=clip_id,
                    error="Failed to generate TTS audio - check OpenAI API key"
                )
            
            # Get audio duration
            duration = await self._get_audio_duration(audio_path)
            
            # Upload to storage
            audio_url = await storage_service.upload_clip_audio(demo_id, clip_id, audio_path)
            
            # Update clip in database
            self.supabase.table("clips").update({
                "narration": request.text,
                "audio_url": audio_url,
                "voice_id": request.voice,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", clip_id).execute()
            
            logger.info(f"Generated narration for clip {clip_id}: {duration}s, voice={request.voice}")
            
            return NarrationResult(
                success=True,
                clip_id=clip_id,
                audio_url=audio_url,
                duration_seconds=duration,
                voice=request.voice
            )
            
        except Exception as e:
            logger.error(f"Failed to generate narration for clip {clip_id}: {e}")
            return NarrationResult(
                success=False,
                clip_id=clip_id,
                error=str(e)
            )

    async def preview_narration(self, text: str, voice: str = "nova", speed: float = 1.0) -> Optional[str]:
        """
        Generate a preview of TTS narration without saving to database.
        Returns base64 encoded audio data.
        """
        try:
            preview_filename = f"preview_{uuid.uuid4().hex[:8]}.mp3"
            audio_path = await audio_service.generate_narration_with_options(
                text=text,
                output_filename=preview_filename,
                voice=voice,
                speed=speed
            )
            
            if not audio_path or not os.path.exists(audio_path):
                return None
            
            # Read and encode audio
            import base64
            with open(audio_path, "rb") as f:
                audio_data = base64.b64encode(f.read()).decode()
            
            # Cleanup preview file
            try:
                os.remove(audio_path)
            except:
                pass
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Failed to generate narration preview: {e}")
            return None

    async def add_text_overlay(self, clip_id: str, overlay: TextOverlay) -> Dict[str, Any]:
        """Add a text overlay to a clip."""
        try:
            # Get clip
            result = self.supabase.table("clips").select("overlay").eq("id", clip_id).single().execute()
            if not result.data:
                return {"success": False, "error": "Clip not found"}
            
            # Get existing overlays or initialize
            existing_overlay = result.data.get("overlay") or {"text_overlays": []}
            if not isinstance(existing_overlay, dict):
                existing_overlay = {"text_overlays": []}
            
            text_overlays = existing_overlay.get("text_overlays", [])
            text_overlays.append(overlay.model_dump())
            existing_overlay["text_overlays"] = text_overlays
            
            # Update clip
            self.supabase.table("clips").update({
                "overlay": existing_overlay,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", clip_id).execute()
            
            return {
                "success": True,
                "overlay_id": overlay.id,
                "clip_id": clip_id
            }
            
        except Exception as e:
            logger.error(f"Failed to add text overlay to clip {clip_id}: {e}")
            return {"success": False, "error": str(e)}

    async def remove_text_overlay(self, clip_id: str, overlay_id: str) -> Dict[str, Any]:
        """Remove a text overlay from a clip."""
        try:
            result = self.supabase.table("clips").select("overlay").eq("id", clip_id).single().execute()
            if not result.data:
                return {"success": False, "error": "Clip not found"}
            
            existing_overlay = result.data.get("overlay") or {"text_overlays": []}
            text_overlays = existing_overlay.get("text_overlays", [])
            
            # Filter out the overlay to remove
            text_overlays = [o for o in text_overlays if o.get("id") != overlay_id]
            existing_overlay["text_overlays"] = text_overlays
            
            self.supabase.table("clips").update({
                "overlay": existing_overlay,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", clip_id).execute()
            
            return {"success": True, "removed_id": overlay_id}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_available_voices(self) -> List[Dict[str, str]]:
        """Get list of available TTS voices with descriptions."""
        return [
            {"id": "alloy", "name": "Alloy", "description": "Neutral and balanced"},
            {"id": "echo", "name": "Echo", "description": "Warm and natural"},
            {"id": "fable", "name": "Fable", "description": "British accent, storytelling"},
            {"id": "onyx", "name": "Onyx", "description": "Deep and authoritative"},
            {"id": "nova", "name": "Nova", "description": "Friendly and conversational"},
            {"id": "shimmer", "name": "Shimmer", "description": "Clear and expressive"},
        ]

    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using ffprobe."""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", audio_path
        ]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return float(stdout.decode().strip())
        except:
            return 0.0


# Global instance
editor_service = EditorService()
