import os
import asyncio
import subprocess
import json
from typing import List, Optional
from ...models.schemas import Clip, Demo
from ...core.database import get_supabase
from ..audio.service import audio_service
from ..storage.service import storage_service

class ExportService:
    def __init__(self):
        self.supabase = get_supabase()
        self.output_dir = "/tmp/autovid/exports"
        os.makedirs(self.output_dir, exist_ok=True)

    async def get_audio_duration(self, audio_path: str) -> float:
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

    async def export_demo(self, demo_id: str) -> Optional[str]:
        # 1. Get clips for the demo
        response = self.supabase.table("clips").select("*").eq("demo_id", demo_id).order("order_index").execute()
        clips_data = response.data
        if not clips_data:
            return None

        # 2. Process each clip: generate audio and combine with video
        processed_clips = []
        for idx, clip_data in enumerate(clips_data):
            clip_id = clip_data["id"]
            video_path = clip_data["video_url"]
            narration = clip_data.get("narration")
            
            # If video_url is a Supabase URL, we might need to download it or handle it.
            # Assuming it's a local path for now during the generation process.
            if not video_path or not os.path.exists(video_path):
                continue
                
            # Generate audio if narration exists
            audio_path = None
            audio_url = None
            if narration:
                audio_filename = f"{demo_id}_clip_{idx}_audio.mp3"
                audio_path = await audio_service.generate_narration(narration, audio_filename)
                if audio_path:
                    audio_url = await storage_service.upload_clip_audio(demo_id, clip_id, audio_path)
            
            # Combine video and audio for this clip
            clip_output_path = os.path.join(self.output_dir, f"{demo_id}_clip_{idx}_final.mp4")
            if audio_path:
                duration = await self.get_audio_duration(audio_path)
                success = await self._combine_video_audio(video_path, audio_path, clip_output_path, duration)
                if success:
                    # Upload clip video to storage
                    video_url = await storage_service.upload_clip_video(demo_id, clip_id, clip_output_path)
                    processed_clips.append(clip_output_path)
                    
                    # Update clip with public URLs
                    self.supabase.table("clips").update({
                        "audio_url": audio_url,
                        "video_url": video_url
                    }).eq("id", clip_id).execute()
                else:
                    processed_clips.append(video_path)
            else:
                processed_clips.append(video_path)

        if not processed_clips:
            return None

        # 3. Concatenate all processed clips
        final_output_path = os.path.join(self.output_dir, f"{demo_id}_final.mp4")
        success = await self._concatenate_clips(processed_clips, final_output_path)
        
        if success:
            # Upload final video to storage
            final_video_url = await storage_service.upload_final_video(demo_id, final_output_path)
            
            # Update demo with final video URL
            self.supabase.table("demos").update({
                "video_url": final_video_url,
                "status": "completed"
            }).eq("id", demo_id).execute()
            return final_video_url
        
        return None

    async def _combine_video_audio(self, video_path: str, audio_path: str, output_path: str, duration: float) -> bool:
        # Use tpad filter to clone the last frame to match audio duration
        # filter_complex handles video padding and audio mapping
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-filter_complex", f"[0:v]tpad=stop_mode=clone:stop_duration={duration}[v]",
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode()}")
            return process.returncode == 0
        except Exception as e:
            print(f"FFmpeg error: {e}")
            return False

    async def _concatenate_clips(self, clip_paths: List[str], output_path: str) -> bool:
        if not clip_paths:
            return False
            
        # Create a file list for ffmpeg concat
        list_path = os.path.join(self.output_dir, "concat_list.txt")
        with open(list_path, "w") as f:
            for path in clip_paths:
                f.write(f"file '{path}'\n")
        
        # We re-encode to ensure consistency across clips (resolutions/framerates)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            output_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception as e:
            print(f"FFmpeg concat error: {e}")
            return False

export_service = ExportService()
