import os
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "AutoVidAI Backend"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    DATABASE_URL: Optional[str] = None
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    
    REDIS_URL: Optional[str] = None
    
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
    
    @field_validator('SUPABASE_URL', mode='before')
    @classmethod
    def get_supabase_url(cls, v):
        return v or os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    
    @field_validator('SUPABASE_ANON_KEY', mode='before')
    @classmethod
    def get_supabase_anon_key(cls, v):
        return v or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
    
    @field_validator('DATABASE_URL', mode='before')
    @classmethod
    def get_database_url(cls, v):
        return v or os.getenv('DATABASE_URL')
    
    @field_validator('SUPABASE_SERVICE_ROLE_KEY', mode='before')
    @classmethod
    def get_supabase_service_role_key(cls, v):
        return v or os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
