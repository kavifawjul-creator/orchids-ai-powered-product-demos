"""
Subtitle Generation Service

Generates SRT/VTT subtitles from narration audio files using Whisper API
and embeds them into videos using FFmpeg.
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class SubtitleEntry:
    """Represents a single subtitle entry with timing and text."""
    
    def __init__(
        self,
        index: int,
        start_time: float,
        end_time: float,
        text: str
    ):
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text
    
    def to_srt(self) -> str:
        """Convert to SRT format."""
        return f"{self.index}\n{self._format_time_srt(self.start_time)} --> {self._format_time_srt(self.end_time)}\n{self.text}\n"
    
    def to_vtt(self) -> str:
        """Convert to VTT format.""" 
        return f"{self._format_time_vtt(self.start_time)} --> {self._format_time_vtt(self.end_time)}\n{self.text}\n"
    
    @staticmethod
    def _format_time_srt(seconds: float) -> str:
        """Format seconds to SRT timestamp (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
    
    @staticmethod
    def _format_time_vtt(seconds: float) -> str:
        """Format seconds to VTT timestamp (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


class SubtitleService:
    """
    Service for generating and embedding subtitles into videos.
    
    Uses OpenAI Whisper API for speech-to-text transcription
    and FFmpeg for subtitle embedding.
    """
    
    def __init__(self):
        self._openai: Optional[AsyncOpenAI] = None
        self._output_dir = "/tmp/autovid/subtitles"
        os.makedirs(self._output_dir, exist_ok=True)
    
    @property
    def openai(self) -> AsyncOpenAI:
        if self._openai is None:
            self._openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai
    
    async def generate_subtitles_from_audio(
        self,
        audio_path: str,
        language: str = "en"
    ) -> List[SubtitleEntry]:
        """
        Transcribe audio file and generate subtitle entries using Whisper.
        
        Args:
            audio_path: Path to audio file (mp3, wav, etc.)
            language: Language code (en, es, fr, etc.)
        
        Returns:
            List of SubtitleEntry objects with timing
        """
        if not os.path.exists(audio_path):
            logger.error(f"Audio file not found: {audio_path}")
            return []
        
        if not settings.OPENAI_API_KEY:
            logger.warning("No OpenAI API key, cannot generate subtitles")
            return []
        
        try:
            with open(audio_path, "rb") as audio_file:
                # Use verbose_json to get word-level timestamps
                response = await self.openai.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            subtitles = []
            for i, segment in enumerate(response.segments or [], 1):
                subtitles.append(SubtitleEntry(
                    index=i,
                    start_time=segment.get("start", 0),
                    end_time=segment.get("end", 0),
                    text=segment.get("text", "").strip()
                ))
            
            return subtitles
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return []
    
    async def generate_subtitles_from_text(
        self,
        narration_text: str,
        total_duration: float,
        words_per_second: float = 2.5
    ) -> List[SubtitleEntry]:
        """
        Generate subtitles from text when no audio is available.
        Estimates timing based on text length.
        
        Args:
            narration_text: The narration text
            total_duration: Total duration in seconds
            words_per_second: Estimated speaking rate
        
        Returns:
            List of SubtitleEntry objects
        """
        if not narration_text:
            return []
        
        # Split into sentences
        sentences = []
        for part in narration_text.replace("!", ".").replace("?", ".").split("."):
            part = part.strip()
            if part:
                sentences.append(part + ".")
        
        if not sentences:
            return []
        
        # Calculate time per sentence based on word count
        total_words = sum(len(s.split()) for s in sentences)
        time_per_word = total_duration / max(total_words, 1)
        
        subtitles = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences, 1):
            word_count = len(sentence.split())
            duration = word_count * time_per_word
            
            subtitles.append(SubtitleEntry(
                index=i,
                start_time=current_time,
                end_time=min(current_time + duration, total_duration),
                text=sentence
            ))
            
            current_time += duration
        
        return subtitles
    
    async def save_srt(
        self,
        subtitles: List[SubtitleEntry],
        output_path: str
    ) -> bool:
        """Save subtitles to SRT file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for entry in subtitles:
                    f.write(entry.to_srt() + "\n")
            logger.info(f"Saved SRT to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save SRT: {e}")
            return False
    
    async def save_vtt(
        self,
        subtitles: List[SubtitleEntry],
        output_path: str
    ) -> bool:
        """Save subtitles to VTT file."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("WEBVTT\n\n")
                for entry in subtitles:
                    f.write(entry.to_vtt() + "\n")
            logger.info(f"Saved VTT to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save VTT: {e}")
            return False
    
    async def embed_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        style: Optional[str] = None
    ) -> bool:
        """
        Embed subtitles into video using FFmpeg.
        
        Args:
            video_path: Path to input video
            subtitle_path: Path to SRT/VTT file
            output_path: Path for output video
            style: Optional ASS style string for customization
        
        Returns:
            True if successful
        """
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        if not os.path.exists(subtitle_path):
            logger.error(f"Subtitle file not found: {subtitle_path}")
            return False
        
        # Build FFmpeg command
        # Using subtitles filter for soft-embedded subs
        subtitle_filter = f"subtitles='{subtitle_path}'"
        
        if style:
            subtitle_filter += f":force_style='{style}'"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vf", subtitle_filter,
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
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
                logger.error(f"FFmpeg subtitle embedding failed: {stderr.decode()}")
                return False
            
            logger.info(f"Embedded subtitles into {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Subtitle embedding error: {e}")
            return False
    
    async def process_clip_subtitles(
        self,
        clip_id: str,
        video_path: str,
        narration_text: str,
        audio_path: Optional[str] = None,
        duration: float = 10.0
    ) -> Optional[str]:
        """
        Full subtitle processing pipeline for a clip.
        
        1. Generate subtitles (from audio or text)
        2. Save SRT file
        3. Embed into video
        4. Return output path
        """
        # Generate subtitles
        if audio_path and os.path.exists(audio_path):
            subtitles = await self.generate_subtitles_from_audio(audio_path)
        else:
            subtitles = await self.generate_subtitles_from_text(narration_text, duration)
        
        if not subtitles:
            logger.warning(f"No subtitles generated for clip {clip_id}")
            return None
        
        # Save SRT
        srt_path = os.path.join(self._output_dir, f"{clip_id}.srt")
        await self.save_srt(subtitles, srt_path)
        
        # Embed into video
        output_path = os.path.join(self._output_dir, f"{clip_id}_subtitled.mp4")
        success = await self.embed_subtitles(video_path, srt_path, output_path)
        
        if success:
            return output_path
        return None


# Global instance
subtitle_service = SubtitleService()
