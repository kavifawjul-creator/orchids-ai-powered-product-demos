import os
import asyncio
from typing import Optional
from openai import AsyncOpenAI
from ...core.config import settings

class AudioService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.audio_dir = "/tmp/autovid/audio"
        os.makedirs(self.audio_dir, exist_ok=True)
        self.voice = "alloy"  # alloy, echo, fable, onyx, nova, shimmer

    async def generate_narration(self, text: str, output_filename: str) -> Optional[str]:
        if not settings.OPENAI_API_KEY:
            return None

        output_path = os.path.join(self.audio_dir, output_filename)
        
        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text
            )
            
            # Use aiofiles if available, otherwise standard write
            # Since we are in an async method, we should avoid blocking
            # but simple file write is usually fast enough for small audio
            await asyncio.to_thread(response.stream_to_file, output_path)
            
            return output_path
        except Exception as e:
            print(f"Error generating TTS: {e}")
            return None

audio_service = AudioService()
