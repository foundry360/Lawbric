"""
Legal Discovery AI Platform - Main FastAPI Application

This is the entry point for the backend API server.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import api_router
from app.core.security import verify_token
from app.models.user import User
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO if settings.ENVIRONMENT == "development" else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Legal Discovery AI Platform...")
    # #region agent log
    import json
    from datetime import datetime
    log_path = r"c:\LegalAI\.cursor\debug.log"
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:35","message":"Lifespan startup beginning","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized")
        # #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:42","message":"Database metadata created","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, "a") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:47","message":"Database creation failed","data":{"error":str(e)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        raise

    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"startup","hypothesisId":"E","location":"main.py:50","message":"Lifespan startup complete, yielding","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    yield
    
    # Shutdown
    logger.info("Shutting down Legal Discovery AI Platform...")
    # #region agent log
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"shutdown","hypothesisId":"E","location":"main.py:58","message":"Lifespan shutdown","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion


# Create FastAPI app
app = FastAPI(
    title="Legal Discovery AI Platform",
    description="AI-powered legal document discovery and analysis platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT == "development" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency for authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Verify JWT token and return current user"""
    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    # In production, fetch user from database
    # For MVP, we'll use a simplified approach
    return User(id=user_id, email=payload.get("email", "user@example.com"))


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {"status": "healthy", "service": "Legal Discovery AI Platform"}
    except Exception as e:
        logger.error(f"Health check error: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


# Include API routes
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9000,
        reload=settings.ENVIRONMENT == "development",
    )

