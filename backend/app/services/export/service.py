import os
import asyncio
import subprocess
from typing import List, Optional
from ...models.schemas import Clip, Demo
from ...core.database import get_supabase
from ..audio.service import audio_service

class ExportService:
    def __init__(self):
        self.supabase = get_supabase()
        self.output_dir = "/tmp/autovid/exports"
        os.makedirs(self.output_dir, exist_ok=True)

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
            
            if not video_path or not os.path.exists(video_path):
                continue
                
            # Generate audio if narration exists
            audio_path = None
            if narration:
                audio_filename = f"{demo_id}_clip_{idx}_audio.mp3"
                audio_path = await audio_service.generate_narration(narration, audio_filename)
            
            # Combine video and audio for this clip
            clip_output_path = os.path.join(self.output_dir, f"{demo_id}_clip_{idx}_final.mp4")
            if audio_path:
                success = await self._combine_video_audio(video_path, audio_path, clip_output_path)
                if success:
                    processed_clips.append(clip_output_path)
                    # Update clip with audio/video urls
                    self.supabase.table("clips").update({
                        "audio_url": audio_path,
                        "video_url": clip_output_path
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
            # Update demo with final video URL
            self.supabase.table("demos").update({
                "video_url": final_output_path,
                "status": "completed"
            }).eq("id", demo_id).execute()
            return final_output_path
        
        return None

    async def _combine_video_audio(self, video_path: str, audio_path: str, output_path: str) -> bool:
        # Use ffmpeg to combine video and audio
        # We also need to ensure the video is long enough for the audio
        # Using -shortest would cut the audio, but we want to see the whole video
        # Actually, for clips, the video should match the narration duration roughly
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",  # For now, just cut to shortest. Better logic later.
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
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
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
