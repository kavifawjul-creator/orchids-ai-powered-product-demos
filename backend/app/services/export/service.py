import os
import asyncio
import subprocess
import json
from typing import List, Optional, Dict, Any
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

        # 2. Process each clip: apply trimming, handle audio
        processed_clips = []
        for idx, clip_data in enumerate(clips_data):
            clip_id = clip_data["id"]
            video_path = clip_data["video_url"]
            narration = clip_data.get("narration")
            trim_start = clip_data.get("trim_start", 0) or 0
            trim_end = clip_data.get("trim_end")
            existing_audio = clip_data.get("audio_url")
            
            # If video_url is a Supabase URL, we might need to download it or handle it.
            # Assuming it's a local path for now during the generation process.
            if not video_path or not os.path.exists(video_path):
                continue
            
            # Apply trimming if specified
            trimmed_video_path = video_path
            if trim_start > 0 or trim_end:
                trimmed_video_path = os.path.join(self.output_dir, f"{demo_id}_clip_{idx}_trimmed.mp4")
                trim_success = await self._trim_video(video_path, trimmed_video_path, trim_start, trim_end)
                if not trim_success:
                    trimmed_video_path = video_path  # Fallback to original
                
            # Get or generate audio
            audio_path = None
            audio_url = existing_audio
            if narration and not existing_audio:
                audio_filename = f"{demo_id}_clip_{idx}_audio.mp3"
                audio_path = await audio_service.generate_narration(narration, audio_filename)
                if audio_path:
                    audio_url = await storage_service.upload_clip_audio(demo_id, clip_id, audio_path)
            elif existing_audio and existing_audio.startswith("/tmp"):
                # Use existing local audio path
                audio_path = existing_audio if os.path.exists(existing_audio) else None
            
            # Combine video and audio for this clip
            clip_output_path = os.path.join(self.output_dir, f"{demo_id}_clip_{idx}_final.mp4")
            if audio_path:
                duration = await self.get_audio_duration(audio_path)
                success = await self._combine_video_audio(trimmed_video_path, audio_path, clip_output_path, duration)
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
                    processed_clips.append(trimmed_video_path)
            else:
                processed_clips.append(trimmed_video_path)

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

    async def _trim_video(
        self, 
        input_path: str, 
        output_path: str, 
        start_time: float, 
        end_time: Optional[float] = None
    ) -> bool:
        """
        Trim a video file using FFmpeg.
        
        Args:
            input_path: Path to source video
            output_path: Path for trimmed video
            start_time: Start time in seconds
            end_time: End time in seconds (None = end of video)
        
        Returns:
            True if successful
        """
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),  # Seek to start time (fast)
            "-i", input_path,
        ]
        
        if end_time:
            # Duration = end_time - start_time
            duration = end_time - start_time
            cmd.extend(["-t", str(duration)])
        
        cmd.extend([
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            output_path
        ])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                print(f"FFmpeg trim error: {stderr.decode()}")
            return process.returncode == 0
        except Exception as e:
            print(f"FFmpeg trim error: {e}")
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

    async def export_demo_with_options(
        self,
        demo_id: str,
        output_format: str = "mp4",
        resolution: str = "1080p",
        include_subtitles: bool = False,
        subtitle_style: str = "default"
    ) -> Optional[str]:
        """
        Export demo with format and resolution options.
        
        Args:
            demo_id: Demo ID to export
            output_format: "mp4", "webm", or "gif"
            resolution: "720p", "1080p", or "4k"
            include_subtitles: Whether to embed subtitles
            subtitle_style: Subtitle styling preset
        
        Returns:
            URL to exported video
        """
        # Map resolution to FFmpeg scale
        resolution_map = {
            "720p": "1280:720",
            "1080p": "1920:1080",
            "4k": "3840:2160"
        }
        scale = resolution_map.get(resolution, "1920:1080")
        
        # First do standard export
        mp4_path = await self.export_demo(demo_id)
        if not mp4_path:
            return None
        
        # If MP4 requested without subtitles, return as-is
        if output_format == "mp4" and not include_subtitles:
            return mp4_path
        
        # Get local path from URL if needed
        if mp4_path.startswith("http"):
            # For cloud URLs, we'd need to download - for now skip format conversion
            return mp4_path
        
        final_path = mp4_path
        
        # Add subtitles if requested
        if include_subtitles:
            from ..subtitle.service import subtitle_service
            
            # Get narration text for subtitles
            response = self.supabase.table("clips").select("*").eq("demo_id", demo_id).order("order_index").execute()
            clips_data = response.data
            
            if clips_data:
                # Combine all narrations
                full_narration = " ".join([c.get("narration", "") for c in clips_data if c.get("narration")])
                
                if full_narration:
                    # Generate subtitles from text
                    subtitles = await subtitle_service.generate_subtitles_from_text(
                        full_narration,
                        total_duration=60.0  # Estimate, could calculate from clips
                    )
                    
                    if subtitles:
                        srt_path = os.path.join(self.output_dir, f"{demo_id}.srt")
                        await subtitle_service.save_srt(subtitles, srt_path)
                        
                        subtitled_path = os.path.join(self.output_dir, f"{demo_id}_subtitled.mp4")
                        success = await subtitle_service.embed_subtitles(
                            mp4_path, srt_path, subtitled_path
                        )
                        if success:
                            final_path = subtitled_path
        
        # Convert format if needed
        if output_format != "mp4":
            converted_path = await self._convert_format(final_path, output_format, scale)
            if converted_path:
                final_path = converted_path
        
        # Upload and update database
        final_url = await storage_service.upload_final_video(demo_id, final_path)
        if final_url:
            self.supabase.table("demos").update({
                "video_url": final_url,
                "export_format": output_format,
                "export_resolution": resolution
            }).eq("id", demo_id).execute()
        
        return final_url
    
    async def _convert_format(
        self,
        input_path: str,
        output_format: str,
        scale: str = "1920:1080"
    ) -> Optional[str]:
        """Convert video to different format."""
        
        if output_format == "webm":
            output_path = input_path.replace(".mp4", ".webm")
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-c:v", "libvpx-vp9",
                "-crf", "30",
                "-b:v", "0",
                "-c:a", "libopus",
                "-vf", f"scale={scale}",
                output_path
            ]
        elif output_format == "gif":
            output_path = input_path.replace(".mp4", ".gif")
            # Generate palette for better GIF quality
            palette_path = input_path.replace(".mp4", "_palette.png")
            
            # Step 1: Generate palette
            palette_cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-vf", f"fps=10,scale=640:-1:flags=lanczos,palettegen",
                palette_path
            ]
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *palette_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
            except:
                pass
            
            # Step 2: Create GIF with palette
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-i", palette_path,
                "-lavfi", f"fps=10,scale=640:-1:flags=lanczos[x];[x][1:v]paletteuse",
                output_path
            ]
        else:
            return None
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return output_path
            return None
        except Exception as e:
            print(f"Format conversion error: {e}")
            return None

    async def apply_transition(
        self,
        clip1_path: str,
        clip2_path: str,
        output_path: str,
        transition_type: str = "dissolve",
        duration: float = 0.5
    ) -> bool:
        """
        Apply a transition effect between two clips.
        
        Args:
            clip1_path: First video clip path
            clip2_path: Second video clip path
            output_path: Output path for combined video
            transition_type: "dissolve", "fade", "wipe_left", "wipe_right"
            duration: Transition duration in seconds
        
        Returns:
            True if successful
        """
        # Get durations of both clips
        dur1 = await self.get_video_duration(clip1_path)
        dur2 = await self.get_video_duration(clip2_path)
        
        if dur1 == 0 or dur2 == 0:
            return False
        
        # Build FFmpeg filter based on transition type
        offset = dur1 - duration
        
        if transition_type == "fade":
            # Simple crossfade
            filter_complex = (
                f"[0:v]trim=0:{dur1},setpts=PTS-STARTPTS[v0];"
                f"[1:v]trim=0:{dur2},setpts=PTS-STARTPTS[v1];"
                f"[v0][v1]xfade=transition=fade:duration={duration}:offset={offset}[outv];"
                f"[0:a][1:a]acrossfade=d={duration}[outa]"
            )
        elif transition_type == "dissolve":
            filter_complex = (
                f"[0:v][1:v]xfade=transition=dissolve:duration={duration}:offset={offset}[outv];"
                f"[0:a][1:a]acrossfade=d={duration}[outa]"
            )
        elif transition_type == "wipe_left":
            filter_complex = (
                f"[0:v][1:v]xfade=transition=wipeleft:duration={duration}:offset={offset}[outv];"
                f"[0:a][1:a]acrossfade=d={duration}[outa]"
            )
        elif transition_type == "wipe_right":
            filter_complex = (
                f"[0:v][1:v]xfade=transition=wiperight:duration={duration}:offset={offset}[outv];"
                f"[0:a][1:a]acrossfade=d={duration}[outa]"
            )
        elif transition_type == "slide_left":
            filter_complex = (
                f"[0:v][1:v]xfade=transition=slideleft:duration={duration}:offset={offset}[outv];"
                f"[0:a][1:a]acrossfade=d={duration}[outa]"
            )
        else:
            # Default to dissolve
            filter_complex = (
                f"[0:v][1:v]xfade=transition=dissolve:duration={duration}:offset={offset}[outv];"
                f"[0:a][1:a]acrossfade=d={duration}[outa]"
            )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", clip1_path,
            "-i", clip2_path,
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-map", "[outa]",
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
            print(f"Transition error: {e}")
            return False

    async def add_background_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        music_volume: float = 0.15,
        fade_in: float = 2.0,
        fade_out: float = 3.0
    ) -> bool:
        """
        Add background music to a video with volume control.
        
        Args:
            video_path: Input video path
            music_path: Background music audio path
            output_path: Output video path
            music_volume: Music volume (0.0-1.0, default 0.15 for subtle)
            fade_in: Fade in duration at start
            fade_out: Fade out duration at end
        
        Returns:
            True if successful
        """
        video_duration = await self.get_video_duration(video_path)
        
        # Build audio filter: loop music, set volume, apply fades, mix with original
        audio_filter = (
            f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{video_duration},"
            f"volume={music_volume},"
            f"afade=t=in:st=0:d={fade_in},"
            f"afade=t=out:st={video_duration - fade_out}:d={fade_out}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-filter_complex", audio_filter,
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
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
            return process.returncode == 0
        except Exception as e:
            print(f"Background music error: {e}")
            return False

    async def add_watermark(
        self,
        video_path: str,
        output_path: str,
        watermark_text: str = "AutoVidAI",
        position: str = "bottom_right",
        opacity: float = 0.5,
        font_size: int = 24
    ) -> bool:
        """
        Add a text watermark to video.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            watermark_text: Watermark text
            position: "top_left", "top_right", "bottom_left", "bottom_right"
            opacity: Text opacity (0.0-1.0)
            font_size: Font size
        
        Returns:
            True if successful
        """
        # Position mapping
        position_map = {
            "top_left": "x=20:y=20",
            "top_right": "x=w-tw-20:y=20",
            "bottom_left": "x=20:y=h-th-20",
            "bottom_right": "x=w-tw-20:y=h-th-20",
            "center": "x=(w-tw)/2:y=(h-th)/2"
        }
        
        pos = position_map.get(position, position_map["bottom_right"])
        alpha = opacity
        
        # Use drawtext filter
        drawtext_filter = (
            f"drawtext=text='{watermark_text}':"
            f"fontsize={font_size}:fontcolor=white@{alpha}:"
            f"{pos}:font=Arial"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", drawtext_filter,
            "-c:v", "libx264",
            "-c:a", "copy",
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
            print(f"Watermark error: {e}")
            return False

    async def change_aspect_ratio(
        self,
        video_path: str,
        output_path: str,
        aspect_ratio: str = "16:9"
    ) -> bool:
        """
        Change video aspect ratio with letterboxing/pillarboxing.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            aspect_ratio: Target aspect ratio ("16:9", "9:16", "1:1", "4:3")
        
        Returns:
            True if successful
        """
        # Resolution mappings for different aspect ratios
        resolution_map = {
            "16:9": "1920:1080",
            "9:16": "1080:1920",  # Portrait/vertical video
            "1:1": "1080:1080",   # Square
            "4:3": "1440:1080",
            "21:9": "2560:1080"   # Ultrawide
        }
        
        target = resolution_map.get(aspect_ratio, "1920:1080")
        width, height = target.split(":")
        
        # Use pad filter with automatic centering and black background
        scale_filter = (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", scale_filter,
            "-c:v", "libx264",
            "-c:a", "copy",
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
            print(f"Aspect ratio change error: {e}")
            return False

    async def get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
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

    async def add_click_effects(
        self,
        video_path: str,
        output_path: str,
        click_events: List[Dict[str, Any]],
        effect_style: str = "ripple"
    ) -> bool:
        """
        Add click effect overlays to video at specified timestamps and positions.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            click_events: List of {timestamp: float, x: int, y: int} dicts
            effect_style: "ripple", "circle", "highlight"
        
        Returns:
            True if successful
        """
        if not click_events:
            # No clicks, just copy the video
            import shutil
            shutil.copy(video_path, output_path)
            return True
        
        # Build filter chain for click effects
        # Each click creates a brief animated circle at the click position
        filter_parts = []
        
        for i, event in enumerate(click_events):
            timestamp = event.get("timestamp", 0)
            x = event.get("x", 100)
            y = event.get("y", 100)
            duration = 0.3  # Click animation duration
            
            if effect_style == "ripple":
                # Expanding circle effect
                filter_parts.append(
                    f"drawbox=x={x-25}:y={y-25}:w=50:h=50:color=yellow@0.5:"
                    f"enable='between(t,{timestamp},{timestamp + duration})',"
                    f"drawbox=x={x-35}:y={y-35}:w=70:h=70:color=yellow@0.3:"
                    f"enable='between(t,{timestamp + 0.1},{timestamp + duration})'"
                )
            elif effect_style == "circle":
                # Simple circle
                filter_parts.append(
                    f"drawbox=x={x-20}:y={y-20}:w=40:h=40:color=red@0.6:t=3:"
                    f"enable='between(t,{timestamp},{timestamp + duration})'"
                )
            else:  # highlight
                # Highlight spot
                filter_parts.append(
                    f"drawbox=x={x-30}:y={y-30}:w=60:h=60:color=white@0.4:"
                    f"enable='between(t,{timestamp},{timestamp + duration})'"
                )
        
        if not filter_parts:
            import shutil
            shutil.copy(video_path, output_path)
            return True
        
        filter_complex = ",".join(filter_parts)
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:v", "libx264",
            "-c:a", "copy",
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
            print(f"Click effects error: {e}")
            return False

    async def apply_zoom_pan(
        self,
        video_path: str,
        output_path: str,
        zoom_type: str = "slow_zoom_in",
        zoom_factor: float = 1.2
    ) -> bool:
        """
        Apply Ken Burns style zoom/pan effect to video.
        
        Args:
            video_path: Input video path
            output_path: Output video path
            zoom_type: "slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right"
            zoom_factor: Zoom multiplier (1.0 = no zoom, 1.2 = 20% zoom)
        
        Returns:
            True if successful
        """
        duration = await self.get_video_duration(video_path)
        if duration == 0:
            return False
        
        # Calculate zoom parameters
        # z=zoom level, zoompan expects values > 1 for zoom in
        if zoom_type == "slow_zoom_in":
            # Start at 1.0, end at zoom_factor
            zoom_expr = f"zoom+{(zoom_factor - 1) / (duration * 25)}"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif zoom_type == "slow_zoom_out":
            # Start at zoom_factor, end at 1.0
            zoom_expr = f"if(lte(zoom,1.0),{zoom_factor},max(1.001,zoom-{(zoom_factor - 1) / (duration * 25)}))"
            x_expr = "iw/2-(iw/zoom/2)"
            y_expr = "ih/2-(ih/zoom/2)"
        elif zoom_type == "pan_left":
            # Pan from right to left
            zoom_expr = f"{zoom_factor}"
            x_expr = f"iw-iw/zoom-({duration}*on/{duration * 25})"
            y_expr = "ih/2-(ih/zoom/2)"
        elif zoom_type == "pan_right":
            # Pan from left to right
            zoom_expr = f"{zoom_factor}"
            x_expr = f"on/{duration * 25}*{duration}"
            y_expr = "ih/2-(ih/zoom/2)"
        else:
            zoom_expr = "1"
            x_expr = "0"
            y_expr = "0"
        
        # Use zoompan filter
        filter_complex = (
            f"zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':"
            f"d={int(duration * 25)}:s=1920x1080:fps=25"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", filter_complex,
            "-c:v", "libx264",
            "-c:a", "copy",
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
            return process.returncode == 0
        except Exception as e:
            print(f"Zoom/pan error: {e}")
            return False

    async def generate_intro(
        self,
        output_path: str,
        title: str,
        subtitle: str = "",
        duration: float = 3.0,
        bg_color: str = "black",
        text_color: str = "white",
        brand_color: str = "#7c3aed"
    ) -> bool:
        """
        Generate a simple intro video with title and subtitle.
        
        Args:
            output_path: Output video path
            title: Main title text
            subtitle: Optional subtitle
            duration: Intro duration in seconds
            bg_color: Background color
            text_color: Text color
            brand_color: Accent color for underline
        
        Returns:
            True if successful
        """
        # Create a colored background with text overlay
        # Using FFmpeg's lavfi source
        
        title_escaped = title.replace("'", "\\'").replace(":", "\\:")
        subtitle_escaped = subtitle.replace("'", "\\'").replace(":", "\\:") if subtitle else ""
        
        filter_chain = (
            f"color=c={bg_color}:s=1920x1080:d={duration},"
            f"drawtext=text='{title_escaped}':"
            f"fontsize=72:fontcolor={text_color}:x=(w-tw)/2:y=(h-th)/2-50:"
            f"font=Arial:fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        )
        
        if subtitle:
            filter_chain += (
                f",drawtext=text='{subtitle_escaped}':"
                f"fontsize=32:fontcolor={text_color}@0.7:x=(w-tw)/2:y=(h-th)/2+50:"
                f"font=Arial"
            )
        
        # Add animated underline
        filter_chain += (
            f",drawbox=x='(w-400)/2':y='h/2+20':w='min(400,400*t/{duration/2})':h=4:"
            f"color={brand_color}@0.8:t=fill"
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", filter_chain,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
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
            print(f"Intro generation error: {e}")
            return False

    async def generate_outro(
        self,
        output_path: str,
        cta_text: str = "Try it now!",
        url: str = "",
        duration: float = 4.0,
        bg_color: str = "black",
        text_color: str = "white"
    ) -> bool:
        """
        Generate an outro video with call-to-action.
        
        Args:
            output_path: Output video path
            cta_text: Call to action text
            url: Optional URL to display
            duration: Outro duration in seconds
            bg_color: Background color
            text_color: Text color
        
        Returns:
            True if successful
        """
        cta_escaped = cta_text.replace("'", "\\'").replace(":", "\\:")
        url_escaped = url.replace("'", "\\'").replace(":", "\\:") if url else ""
        
        filter_chain = (
            f"color=c={bg_color}:s=1920x1080:d={duration},"
            f"drawtext=text='{cta_escaped}':"
            f"fontsize=64:fontcolor={text_color}:x=(w-tw)/2:y=(h-th)/2-30:"
            f"font=Arial"
        )
        
        if url:
            filter_chain += (
                f",drawtext=text='{url_escaped}':"
                f"fontsize=36:fontcolor={text_color}@0.6:x=(w-tw)/2:y=(h-th)/2+50:"
                f"font=Arial"
            )
        
        # Add fade in effect
        filter_chain += ",fade=t=in:st=0:d=0.5"
        
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", filter_chain,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
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
            print(f"Outro generation error: {e}")
            return False



    async def export_with_progress(
        self,
        demo_id: str,
        options: dict = None,
        progress_callback = None
    ) -> Optional[str]:
        """
        Export demo with progress updates.
        
        Args:
            demo_id: Demo ID to export
            options: Export options dict with keys:
                - format: "mp4", "webm", "gif"
                - resolution: "720p", "1080p", "4k"
                - aspect_ratio: "16:9", "9:16", "1:1"
                - include_subtitles: bool
                - background_music: path to music file
                - music_volume: 0.0-1.0
                - watermark: text or None
                - transitions: bool (apply transitions between clips)
                - transition_type: "fade", "dissolve", etc.
            progress_callback: async function(step: str, percent: int)
        
        Returns:
            URL to exported video
        """
        options = options or {}
        
        async def report_progress(step: str, percent: int):
            if progress_callback:
                await progress_callback(step, percent)
        
        await report_progress("Starting export", 0)
        
        # Step 1: Get clips
        response = self.supabase.table("clips").select("*").eq("demo_id", demo_id).order("order_index").execute()
        clips_data = response.data
        if not clips_data:
            return None
        
        total_clips = len(clips_data)
        await report_progress("Processing clips", 5)
        
        # Step 2: Process each clip
        processed_clips = []
        for idx, clip_data in enumerate(clips_data):
            clip_progress = 5 + int((idx / total_clips) * 40)
            await report_progress(f"Processing clip {idx + 1}/{total_clips}", clip_progress)
            
            clip_id = clip_data["id"]
            video_path = clip_data.get("video_url", "")
            
            if not video_path or not os.path.exists(video_path):
                continue
            
            # Apply trimming
            trimmed_path = video_path
            if clip_data.get("trim_start", 0) > 0 or clip_data.get("trim_end"):
                trimmed_path = os.path.join(self.output_dir, f"{demo_id}_clip_{idx}_trimmed.mp4")
                await self._trim_video(
                    video_path, trimmed_path,
                    clip_data.get("trim_start", 0),
                    clip_data.get("trim_end")
                )
            
            processed_clips.append(trimmed_path)
        
        if not processed_clips:
            return None
        
        await report_progress("Combining clips", 50)
        
        # Step 3: Concatenate with or without transitions
        combined_path = os.path.join(self.output_dir, f"{demo_id}_combined.mp4")
        
        if options.get("transitions") and len(processed_clips) > 1:
            # Apply transitions between clips
            transition_type = options.get("transition_type", "dissolve")
            temp_path = processed_clips[0]
            
            for i, clip in enumerate(processed_clips[1:], 1):
                await report_progress(f"Applying transition {i}", 50 + int((i / len(processed_clips)) * 10))
                next_temp = os.path.join(self.output_dir, f"{demo_id}_trans_{i}.mp4")
                success = await self.apply_transition(
                    temp_path, clip, next_temp,
                    transition_type=transition_type,
                    duration=0.5
                )
                if success:
                    temp_path = next_temp
            
            combined_path = temp_path
        else:
            # Simple concatenation
            await self._concatenate_clips(processed_clips, combined_path)
        
        current_path = combined_path
        
        # Step 4: Apply aspect ratio if specified
        if options.get("aspect_ratio") and options["aspect_ratio"] != "16:9":
            await report_progress("Adjusting aspect ratio", 65)
            aspect_path = os.path.join(self.output_dir, f"{demo_id}_aspect.mp4")
            if await self.change_aspect_ratio(current_path, aspect_path, options["aspect_ratio"]):
                current_path = aspect_path
        
        # Step 5: Add background music if specified
        if options.get("background_music") and os.path.exists(options["background_music"]):
            await report_progress("Adding background music", 70)
            music_path = os.path.join(self.output_dir, f"{demo_id}_music.mp4")
            if await self.add_background_music(
                current_path, options["background_music"], music_path,
                music_volume=options.get("music_volume", 0.15)
            ):
                current_path = music_path
        
        # Step 6: Add watermark if specified
        if options.get("watermark"):
            await report_progress("Adding watermark", 80)
            watermark_path = os.path.join(self.output_dir, f"{demo_id}_watermark.mp4")
            if await self.add_watermark(
                current_path, watermark_path, options["watermark"]
            ):
                current_path = watermark_path
        
        # Step 7: Convert format if needed
        output_format = options.get("format", "mp4")
        resolution = options.get("resolution", "1080p")
        
        if output_format != "mp4":
            await report_progress(f"Converting to {output_format}", 85)
            resolution_map = {"720p": "1280:720", "1080p": "1920:1080", "4k": "3840:2160"}
            converted_path = await self._convert_format(
                current_path, output_format, resolution_map.get(resolution, "1920:1080")
            )
            if converted_path:
                current_path = converted_path
        
        await report_progress("Uploading", 90)
        
        # Step 8: Upload and update database
        final_url = await storage_service.upload_final_video(demo_id, current_path)
        if final_url:
            self.supabase.table("demos").update({
                "video_url": final_url,
                "export_format": output_format,
                "export_resolution": resolution,
                "status": "completed"
            }).eq("id", demo_id).execute()
        
        await report_progress("Complete", 100)
        
        return final_url


# Background music presets (paths relative to project)
MUSIC_PRESETS = {
    "corporate_minimal": {
        "name": "Corporate Minimal Tech",
        "description": "Subtle, professional background music",
        "duration": 180,
        "bpm": 110
    },
    "upbeat_tech": {
        "name": "Upbeat Technology",
        "description": "Energetic, modern tech vibes",
        "duration": 150,
        "bpm": 128
    },
    "calm_ambient": {
        "name": "Calm Ambient",
        "description": "Relaxing, ambient soundscape",
        "duration": 240,
        "bpm": 80
    },
    "inspiring_piano": {
        "name": "Inspiring Piano",
        "description": "Emotional, piano-driven melody",
        "duration": 200,
        "bpm": 90
    }
}


export_service = ExportService()

