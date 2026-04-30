from __future__ import annotations
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    LOG_LEVEL: str = Field(default="INFO")

    GEMINI_API_KEY: str = Field(..., description="Gemini API key authenticating all gemini models.")
    COGNITO_MODEL: str = Field(..., description="Gemini live bidi model")
    COGNITO_SEARCH_MODEL: str = Field(..., description="Gemini model for search agent")
    COGNITO_IMAGE_MODEL: str = Field(..., description="Gemini model for image generation")

    GCP_PROJECT_ID: str = Field(..., description="Google Cloud Project ID")
    GCP_DATABASE_ID: str = Field(..., description="Google Cloud Firestore Database ID")
    GCP_IMAGE_BUCKET: str = Field(..., description="Google Cloud Storage Bucket for generated images")

    DEFAULT_VOICE_NAME: str = Field(default="Puck")

@lru_cache
def get_settings() -> Settings:
    """Return a cached instance of app settings"""
    return Settings()
