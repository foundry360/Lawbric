"""
Integration endpoints for third-party services (Google Drive, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from urllib.parse import urlencode

from app.core.supabase import get_supabase_client
from app.core.config import settings
from app.core.supabase_db import get_oauth_connection, create_oauth_connection, delete_oauth_connection
from app.services.google_drive_service import GoogleDriveService

router = APIRouter()
security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Get current user ID from Supabase token"""
    token = credentials.credentials
    supabase = get_supabase_client()
    
    if not supabase:
        print("ERROR: Supabase client not available in get_current_user_id")
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        print(f"Verifying token (length: {len(token)})")
        response = supabase.auth.get_user(token)
        if not response.user:
            print("ERROR: No user in response")
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = response.user.id
        print(f"Successfully authenticated user: {user_id}")
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error getting user from token: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.get("/google/authorize")
async def get_google_authorize_url(
    user_id: str = Depends(get_current_user_id)
):
    """Get Google OAuth authorization URL"""
    # Debug: Log what we have (without exposing secrets)
    has_client_id = bool(settings.GOOGLE_CLIENT_ID)
    has_client_secret = bool(settings.GOOGLE_CLIENT_SECRET)
    has_redirect_uri = bool(settings.GOOGLE_REDIRECT_URI)
    
    redirect_uri = settings.GOOGLE_REDIRECT_URI.strip() if settings.GOOGLE_REDIRECT_URI else ""
    
    print("=" * 80)
    print("GOOGLE OAUTH DEBUG INFO")
    print("=" * 80)
    print(f"Client ID configured: {has_client_id}")
    print(f"Client Secret configured: {has_client_secret}")
    print(f"Redirect URI configured: {has_redirect_uri}")
    print(f"Redirect URI value: '{redirect_uri}'")
    print(f"Redirect URI length: {len(redirect_uri)}")
    print(f"Redirect URI repr: {repr(redirect_uri)}")
    print(f"Redirect URI bytes: {redirect_uri.encode('utf-8')}")
    print("=" * 80)
    
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=400, 
            detail=f"Google OAuth not configured. Client ID: {has_client_id}, Client Secret: {has_client_secret}. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your backend/.env file."
        )
    
    if not redirect_uri:
        raise HTTPException(
            status_code=400,
            detail="Google OAuth redirect URI not configured. Please set GOOGLE_REDIRECT_URI in your backend/.env file."
        )
    
    try:
        print(f"Attempting to generate auth URL with redirect_uri: '{redirect_uri}'")
        auth_url = GoogleDriveService.get_authorization_url(redirect_uri)
        print(f"Successfully generated auth URL")
        # Extract redirect_uri from the generated URL to verify what was sent
        if "redirect_uri=" in auth_url:
            import urllib.parse
            parsed = urllib.parse.urlparse(auth_url)
            params = urllib.parse.parse_qs(parsed.query)
            if 'redirect_uri' in params:
                sent_redirect_uri = urllib.parse.unquote(params['redirect_uri'][0])
                print(f"Redirect URI in generated URL: '{sent_redirect_uri}'")
                print(f"Match: {redirect_uri == sent_redirect_uri}")
        print("=" * 80)
        return {"url": auth_url}
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating authorization URL: {e}")
        print(f"Traceback: {error_details}")
        print("=" * 80)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate authorization URL: {str(e)}"
        )


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    user_id: str = Depends(get_current_user_id)
):
    """Handle Google OAuth callback and store tokens"""
    from urllib.parse import unquote
    
    # URL decode the code in case it's encoded
    code = unquote(code)
    
    print("=" * 80)
    print("OAUTH CALLBACK DEBUG")
    print("=" * 80)
    print(f"Received code (decoded): {code[:50]}... (length: {len(code)})")
    print(f"User ID: {user_id}")
    print(f"Google Client ID configured: {bool(settings.GOOGLE_CLIENT_ID)}")
    if settings.GOOGLE_CLIENT_ID:
        print(f"Google Client ID (first 20 chars): {settings.GOOGLE_CLIENT_ID[:20]}...")
    print(f"Google Client Secret configured: {bool(settings.GOOGLE_CLIENT_SECRET)}")
    print(f"Redirect URI from settings: '{settings.GOOGLE_REDIRECT_URI}'")
    print("=" * 80)
    
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    if not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(status_code=500, detail="Google OAuth redirect URI not configured")
    
    try:
        redirect_uri = settings.GOOGLE_REDIRECT_URI.strip()
        
        # Check if connection already exists - if so, we might be retrying with an expired code
        existing_connection = get_oauth_connection(user_id, 'google_drive')
        if existing_connection:
            print(f"WARNING: OAuth connection already exists for user {user_id}. This might be a retry with an expired code.")
            # If the connection exists and is valid, return success
            # Otherwise, we'll try to update it with new tokens
        
        print(f"Exchanging code for tokens with redirect_uri: '{redirect_uri}'")
        print(f"Code length: {len(code)}, Code preview: {code[:20]}...")
        
        tokens = GoogleDriveService.exchange_code_for_tokens(code, redirect_uri)
        print(f"Successfully exchanged code for tokens. Has access_token: {bool(tokens.get('access_token'))}, Has refresh_token: {bool(tokens.get('refresh_token'))}")
        
        # Store connection in database
        print(f"Storing OAuth connection for user: {user_id}")
        connection = create_oauth_connection(
            user_id=user_id,
            provider='google_drive',
            access_token=tokens['access_token'],
            refresh_token=tokens.get('refresh_token'),
            token_expires_at=tokens.get('token_expires_at')
        )
        
        if not connection:
            print("ERROR: create_oauth_connection returned None")
            raise HTTPException(status_code=500, detail="Failed to store OAuth connection")
        
        print(f"Successfully stored OAuth connection: {connection}")
        print("=" * 80)
        return {"status": "connected", "message": "Google Drive connected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("=" * 80)
        print("OAUTH CALLBACK ERROR")
        print("=" * 80)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print(f"Traceback: {error_details}")
        print("=" * 80)
        error_message = str(e)
        if "invalid_grant" in error_message.lower():
            error_message = "Authorization code expired or already used. Please try connecting again."
        elif "redirect_uri_mismatch" in error_message.lower():
            error_message = "Redirect URI mismatch. Please check Google OAuth configuration."
        raise HTTPException(status_code=500, detail=error_message or "Failed to complete OAuth flow")


@router.get("/google/status")
async def get_google_status(
    user_id: str = Depends(get_current_user_id)
):
    """Check if user has connected Google Drive"""
    connection = get_oauth_connection(user_id, 'google_drive')
    return {"connected": connection is not None}


@router.get("/google/client-id")
async def get_google_client_id():
    """Get Google OAuth Client ID for frontend use (public endpoint, no auth required)"""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=404,
            detail="Google OAuth not configured"
        )
    return {"client_id": settings.GOOGLE_CLIENT_ID}


@router.get("/google/access-token")
async def get_google_access_token(
    user_id: str = Depends(get_current_user_id)
):
    """Get current Google Drive access token for Picker API"""
    connection = get_oauth_connection(user_id, 'google_drive')
    if not connection:
        raise HTTPException(status_code=404, detail="Google Drive not connected")
    
    # Check if token needs refresh
    service = GoogleDriveService(user_id)
    access_token = service.get_access_token()
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Failed to get access token")
    
    return {"access_token": access_token}


@router.delete("/google/disconnect")
async def disconnect_google(
    user_id: str = Depends(get_current_user_id)
):
    """Disconnect Google Drive"""
    success = delete_oauth_connection(user_id, 'google_drive')
    if not success:
        raise HTTPException(status_code=500, detail="Failed to disconnect Google Drive")
    return {"status": "disconnected", "message": "Google Drive disconnected successfully"}


@router.get("/google/files")
async def list_google_files(
    folder_id: Optional[str] = Query(None, description="Folder ID to list files from. None for root."),
    user_id: str = Depends(get_current_user_id)
):
    """List files from Google Drive"""
    try:
        service = GoogleDriveService(user_id)
        files = service.list_files(folder_id=folder_id)
        return {"files": files}
    except Exception as e:
        print(f"Error listing Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/files/recent")
async def list_recent_google_files(
    user_id: str = Depends(get_current_user_id)
):
    """List recently accessed files from Google Drive"""
    try:
        service = GoogleDriveService(user_id)
        files = service.list_recent_files()
        return {"files": files}
    except Exception as e:
        print(f"Error listing recent Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/files/shared")
async def list_shared_google_files(
    user_id: str = Depends(get_current_user_id)
):
    """List files shared with the user from Google Drive"""
    try:
        service = GoogleDriveService(user_id)
        files = service.list_shared_files()
        return {"files": files}
    except Exception as e:
        print(f"Error listing shared Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/google/import")
async def import_google_file(
    case_id: str = Query(..., description="Case ID (UUID from Supabase)"),
    file_id: str = Query(..., description="Google Drive file ID"),
    bates_number: Optional[str] = Query(None),
    custodian: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    document_date: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    """Import a file from Google Drive to a case"""
    try:
        from app.core.supabase_db import get_user_profile
        from app.core.database import get_db, SessionLocal
        from app.models.case import Case, Document
        from app.services.document_processor import DocumentProcessor
        from app.services.embedding_service import EmbeddingService
        from app.services.vector_store import VectorStore
        from datetime import datetime
        from pathlib import Path
        import os
        
        # Download file from Google Drive
        service = GoogleDriveService(user_id)
        file_content, filename = service.download_file(file_id)
        file_metadata = service.get_file_metadata(file_id)
        
        # Validate file type
        file_ext = Path(filename).suffix[1:].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type .{file_ext} not allowed. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_size = len(file_content)
        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )
        
        # Note: Since we're using Supabase cases (UUID), we need to handle this differently
        # For now, we'll save the file and create a document record in Supabase
        # The case_id is a UUID string from Supabase
        case_dir = os.path.join(settings.UPLOAD_DIR, f"case_{case_id}")
        os.makedirs(case_dir, exist_ok=True)
        
        file_path = os.path.join(case_dir, filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create document record in Supabase
        supabase = get_supabase_client()
        if not supabase:
            raise HTTPException(status_code=500, detail="Supabase not configured")
        
        document_data = {
            'case_id': case_id,
            'filename': filename,
            'original_filename': filename,
            'file_path': file_path,
            'file_type': file_ext,
            'file_size': file_size,
            'mime_type': file_metadata.get('mimeType'),
            'bates_number': bates_number,
            'custodian': custodian,
            'author': author,
            'document_date': document_date,
            'source': source or 'google_drive',
            'uploaded_by': user_id,
            'status': 'processing'
        }
        
        response = supabase.table('documents').insert(document_data).execute()
        document = response.data[0] if response.data else None
        
        if not document:
            raise HTTPException(status_code=500, detail="Failed to create document record")
        
        # Process document in background (similar to upload endpoint)
        # Note: This would need to be adapted for Supabase document processing
        # For now, we'll return the document
        
        return {
            "id": document['id'],
            "case_id": document['case_id'],
            "filename": document['filename'],
            "original_filename": document['original_filename'],
            "file_type": document['file_type'],
            "file_size": document['file_size'],
            "status": document['status'],
            "message": "File imported from Google Drive successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error importing file from Google Drive: {e}")
        raise HTTPException(status_code=500, detail=str(e))

