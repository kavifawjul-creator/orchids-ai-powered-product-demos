import os
import asyncio
from typing import Optional, Literal
from openai import AsyncOpenAI
from ...core.config import settings

TTS_VOICE_OPTIONS = Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

class AudioService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.audio_dir = "/tmp/autovid/audio"
        os.makedirs(self.audio_dir, exist_ok=True)
    
    @property
    def voice(self) -> str:
        return settings.TTS_VOICE
    
    @property
    def model(self) -> str:
        return settings.TTS_MODEL

    async def generate_narration(
        self, 
        text: str, 
        output_filename: str,
        voice: Optional[TTS_VOICE_OPTIONS] = None
    ) -> Optional[str]:
        if not settings.OPENAI_API_KEY:
            return None

        output_path = os.path.join(self.audio_dir, output_filename)
        selected_voice = voice or self.voice
        
        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=selected_voice,
                input=text
            )
            
            await asyncio.to_thread(response.stream_to_file, output_path)
            
            return output_path
        except Exception as e:
            print(f"Error generating TTS: {e}")
            return None
    
    async def generate_narration_with_options(
        self,
        text: str,
        output_filename: str,
        voice: Optional[TTS_VOICE_OPTIONS] = None,
        speed: float = 1.0
    ) -> Optional[str]:
        if not settings.OPENAI_API_KEY:
            return None

        output_path = os.path.join(self.audio_dir, output_filename)
        selected_voice = voice or self.voice
        speed = max(0.25, min(4.0, speed))
        
        try:
            response = await self.client.audio.speech.create(
                model=self.model,
                voice=selected_voice,
                input=text,
                speed=speed
            )
            
            await asyncio.to_thread(response.stream_to_file, output_path)
            
            return output_path
        except Exception as e:
            print(f"Error generating TTS with options: {e}")
            return None

    @staticmethod
    def get_available_voices() -> list[str]:
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

audio_service = AudioService()
