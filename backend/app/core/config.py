"""
Application configuration using Pydantic settings
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""
    
    # Server
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # Database
    DATABASE_URL: str = "sqlite:///./legalai.db"
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""  # Service role key for backend operations
    
    # Vector Database
    VECTOR_DB_TYPE: str = "chroma"  # Options: pinecone, weaviate, chroma
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "legalai-documents"
    WEAVIATE_URL: str = "http://localhost:8080"
    WEAVIATE_API_KEY: str = ""
    
    # LLM Provider
    LLM_PROVIDER: str = "openai"  # Options: openai, anthropic
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"
    
    # OCR
    OCR_PROVIDER: str = "tesseract"
    TESSERACT_CMD: str = ""
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    THUMBNAIL_DIR: str = "./thumbnails"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: List[str] = [
        "pdf", "docx", "gdoc", "xlsx", "gsheet", "gslides", "pptx",
        "tiff", "tif", "msg", "eml", "xps", "odt", "ods", "epub", "csv",
        "txt", "jpg", "jpeg", "png", "gif", "bmp", "webp"
    ]
    THUMBNAIL_SIZE: int = 400  # Max width/height in pixels
    
    # Security
    ENCRYPT_FILES: bool = True
    CASE_ISOLATION_ENABLED: bool = True
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/connected-apps/callback"
    
    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    class Config:
        # Look for .env file in the backend directory
        # Path: backend/app/core/config.py -> backend/.env
        # Use absolute path to ensure we find the file
        _backend_dir = Path(__file__).parent.parent.parent
        env_file = str(_backend_dir / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Reload .env file on each access (for development)
        # In production, settings are loaded once at startup


# Create settings instance
settings = Settings()

# Ensure upload and thumbnail directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)



