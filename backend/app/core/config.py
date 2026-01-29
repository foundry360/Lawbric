"""
Application configuration using Pydantic settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os
from pathlib import Path
import json
from datetime import datetime

# #region agent log
# Determine log path - works in both Docker and local
_log_path = None
if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER") == "true":
    # Docker: use /tmp or /app
    _log_path = "/tmp/debug.log" if os.path.exists("/tmp") else "/app/debug.log"
else:
    # Local Windows: use .cursor directory
    _log_path = r"c:\LegalAI\.cursor\debug.log"
    # Ensure directory exists
    os.makedirs(os.path.dirname(_log_path), exist_ok=True)
log_path = _log_path
def agent_log(session_id, run_id, hypothesis_id, location, message, data=None):
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":session_id,"runId":run_id,"hypothesisId":hypothesis_id,"location":location,"message":message,"data":data or {},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except Exception as e:
        # Fallback: try to log to stderr
        import sys
        print(f"DEBUG LOG ERROR: {e}", file=sys.stderr)
# #endregion


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
    
    # Risk Engine Configuration
    RISK_ENABLED: bool = True
    RISK_PROFILE_A_MAX: int = 30  # 0-30: Low risk
    RISK_PROFILE_B_MAX: int = 70  # 31-70: Medium risk
    RISK_PROFILE_C_MAX: int = 100  # 71-100: High risk
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/connected-apps/callback"
    
    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    model_config = SettingsConfigDict(
        # Look for .env file in the backend directory
        # Path: backend/app/core/config.py -> backend/.env
        # In Docker, the .env file might be at /app/.env or passed via environment variables
        # Use absolute path to ensure we find the file regardless of working directory
        env_file=str((Path(__file__).parent.parent.parent / ".env").resolve()),
        env_file_encoding="utf-8",
        case_sensitive=True,
        # Environment variables take precedence over .env file (good for Docker)
        # Reload .env file on each access (for development)
        # In production, settings are loaded once at startup
    )
    
    def model_post_init(self, __context):
        # #region agent log
        _env_file_path = str((Path(__file__).parent.parent.parent / ".env").resolve())
        _env_file_exists = os.path.exists(_env_file_path)
        _env_file_readable = os.access(_env_file_path, os.R_OK) if _env_file_exists else False
        _is_docker = os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER") == "true"
        _os_env_has_client_id = bool(os.environ.get("GOOGLE_CLIENT_ID", ""))
        _os_env_has_client_secret = bool(os.environ.get("GOOGLE_CLIENT_SECRET", ""))
        _os_env_client_id_value = os.environ.get("GOOGLE_CLIENT_ID", "")[:30] + "..." if os.environ.get("GOOGLE_CLIENT_ID", "") and len(os.environ.get("GOOGLE_CLIENT_ID", "")) > 30 else (os.environ.get("GOOGLE_CLIENT_ID", "") if os.environ.get("GOOGLE_CLIENT_ID", "") else "EMPTY")
        agent_log("debug-session", "run1", "H2", "config.py:model_post_init", "Settings.model_post_init called - checking .env file and Docker", {
            "env_file_path": _env_file_path,
            "env_file_exists": _env_file_exists,
            "env_file_readable": _env_file_readable,
            "current_dir": str(Path.cwd()),
            "__file__": str(__file__),
            "is_docker": _is_docker,
            "os_env_has_client_id": _os_env_has_client_id,
            "os_env_has_client_secret": _os_env_has_client_secret,
            "os_env_client_id_preview": _os_env_client_id_value,
            "model_config_env_file": self.model_config.get("env_file") if hasattr(self.model_config, "get") else str(self.model_config.env_file) if hasattr(self.model_config, "env_file") else "N/A"
        })
        # #endregion
        # #region agent log
        agent_log("debug-session", "run1", "H1", "config.py:model_post_init", "Settings instance created - values loaded", {
            "has_google_client_id": bool(self.GOOGLE_CLIENT_ID),
            "has_google_client_secret": bool(self.GOOGLE_CLIENT_SECRET),
            "google_client_id_length": len(self.GOOGLE_CLIENT_ID) if self.GOOGLE_CLIENT_ID else 0,
            "google_client_secret_length": len(self.GOOGLE_CLIENT_SECRET) if self.GOOGLE_CLIENT_SECRET else 0,
            "google_redirect_uri": self.GOOGLE_REDIRECT_URI,
            "google_client_id_preview": self.GOOGLE_CLIENT_ID[:30] + "..." if self.GOOGLE_CLIENT_ID and len(self.GOOGLE_CLIENT_ID) > 30 else (self.GOOGLE_CLIENT_ID if self.GOOGLE_CLIENT_ID else "EMPTY")
        })
        # #endregion


# Create settings instance
# #region agent log
agent_log("debug-session", "run1", "H1", "config.py:88", "About to create Settings instance", {
    "env_file_path": str(Path(__file__).parent.parent.parent / ".env"),
    "env_file_exists": os.path.exists(str(Path(__file__).parent.parent.parent / ".env")),
    "os_environ_GOOGLE_CLIENT_ID": bool(os.environ.get("GOOGLE_CLIENT_ID", "")),
    "os_environ_GOOGLE_CLIENT_SECRET": bool(os.environ.get("GOOGLE_CLIENT_SECRET", ""))
})
# #endregion
settings = Settings()
# #region agent log
agent_log("debug-session", "run1", "H1", "config.py:89", "Settings instance created - final values", {
    "has_google_client_id": bool(settings.GOOGLE_CLIENT_ID),
    "has_google_client_secret": bool(settings.GOOGLE_CLIENT_SECRET),
    "google_client_id_preview": settings.GOOGLE_CLIENT_ID[:20] + "..." if settings.GOOGLE_CLIENT_ID and len(settings.GOOGLE_CLIENT_ID) > 20 else (settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else "EMPTY"),
    "google_client_secret_preview": "***" if settings.GOOGLE_CLIENT_SECRET else "EMPTY"
})
# #endregion

# Ensure upload and thumbnail directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.THUMBNAIL_DIR, exist_ok=True)



