import os
from typing import Optional
from ...core.database import get_supabase

class StorageService:
    def __init__(self):
        self.supabase = get_supabase()
        self.bucket_name = "demos"

    async def upload_file(self, file_path: str, destination_path: str) -> Optional[str]:
        """
        Uploads a file to Supabase Storage and returns the public URL.
        """
        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                # Use synchronous upload as the current supabase-py version might not support async well for storage
                # Or if it does, it's often better to wrap it
                response = self.supabase.storage.from_(self.bucket_name).upload(
                    path=destination_path,
                    file=f,
                    file_options={"upsert": "true"}
                )
            
            # Get public URL
            public_url = self.supabase.storage.from_(self.bucket_name).get_public_url(destination_path)
            return public_url
        except Exception as e:
            print(f"Error uploading file to storage: {e}")
            return None

    async def upload_clip_video(self, demo_id: str, clip_id: str, file_path: str) -> Optional[str]:
        destination = f"{demo_id}/clips/{clip_id}.mp4"
        return await self.upload_file(file_path, destination)

    async def upload_clip_audio(self, demo_id: str, clip_id: str, file_path: str) -> Optional[str]:
        destination = f"{demo_id}/audio/{clip_id}.mp3"
        return await self.upload_file(file_path, destination)

    async def upload_final_video(self, demo_id: str, file_path: str) -> Optional[str]:
        destination = f"{demo_id}/final.mp4"
        return await self.upload_file(file_path, destination)

storage_service = StorageService()
