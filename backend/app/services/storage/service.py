import os
import logging
from typing import Optional
from ...core.database import get_supabase

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.supabase = get_supabase()
        self.bucket_name = "demos"

    async def upload_file(self, file_path: str, destination_path: str, content_type: str = "video/webm") -> Optional[str]:
        if not os.path.exists(file_path):
            logger.error(f"File not found for upload: {file_path}")
            return None

        try:
            with open(file_path, "rb") as f:
                file_data = f.read()
            
            response = self.supabase.storage.from_(self.bucket_name).upload(
                path=destination_path,
                file=file_data,
                file_options={"upsert": "true", "content-type": content_type}
            )
            
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(destination_path)
            logger.info(f"Successfully uploaded {file_path} -> {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Error uploading file to storage: {e}")
            return None

    async def upload_clip_video(self, demo_id: str, clip_id: str, file_path: str) -> Optional[str]:
        ext = os.path.splitext(file_path)[1] or ".webm"
        content_type = "video/webm" if ext == ".webm" else "video/mp4"
        destination = f"{demo_id}/clips/{clip_id}{ext}"
        return await self.upload_file(file_path, destination, content_type)

    async def upload_clip_audio(self, demo_id: str, clip_id: str, file_path: str) -> Optional[str]:
        destination = f"{demo_id}/audio/{clip_id}.mp3"
        return await self.upload_file(file_path, destination, "audio/mpeg")

    async def upload_final_video(self, demo_id: str, file_path: str) -> Optional[str]:
        destination = f"{demo_id}/final.mp4"
        return await self.upload_file(file_path, destination, "video/mp4")

    async def extract_thumbnail(self, video_url: str, demo_id: str) -> Optional[str]:
        import subprocess
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                thumb_path = tmp.name
            
            cmd = [
                "ffmpeg", "-y",
                "-i", video_url,
                "-ss", "00:00:02",
                "-vframes", "1",
                "-vf", "scale=640:-1",
                thumb_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode != 0 or not os.path.exists(thumb_path):
                logger.warning(f"FFmpeg failed: {result.stderr.decode()}")
                return None
            
            destination = f"{demo_id}/thumbnail.jpg"
            url = await self.upload_file(thumb_path, destination, "image/jpeg")
            
            try:
                os.unlink(thumb_path)
            except:
                pass
            
            return url
        except Exception as e:
            logger.error(f"Error extracting thumbnail: {e}")
            return None

storage_service = StorageService()
