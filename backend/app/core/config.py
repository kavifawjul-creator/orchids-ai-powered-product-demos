from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AutoVidAI Backend"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    REDIS_URL: str = "redis://localhost:6379"
    
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    DAYTONA_API_KEY: Optional[str] = None
    DAYTONA_API_URL: str = "https://api.daytona.io"
    DAYTONA_TARGET: str = "us"
    
    S3_BUCKET_NAME: str = "autovid-recordings"
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "us-west-2"
    S3_ENDPOINT_URL: Optional[str] = None
    
    TTS_VOICE: str = "alloy"
    TTS_MODEL: str = "tts-1"
    
    SANDBOX_TIMEOUT_MINUTES: int = 30
    MAX_STEPS_PER_SESSION: int = 100
    MAX_BROWSER_TIME_MINUTES: int = 15
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
