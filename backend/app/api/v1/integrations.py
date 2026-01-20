"""
Integration endpoints for third-party services (Google Drive, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
from typing import Optional
from urllib.parse import urlencode
import httpx

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
    # #region agent log
    import json
    from datetime import datetime
    log_path = r"c:\LegalAI\.cursor\debug.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"J","location":"integrations.py:193","message":"Google status check called","data":{"user_id":user_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    try:
        connection = get_oauth_connection(user_id, 'google_drive')
        is_connected = connection is not None
        
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"J","location":"integrations.py:202","message":"Google status check result","data":{"user_id":user_id,"is_connected":is_connected,"has_connection":connection is not None},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        
        return {"connected": is_connected}
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"J","location":"integrations.py:210","message":"Google status check error","data":{"user_id":user_id,"error":str(e),"error_type":type(e).__name__},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        print(f"Error checking Google Drive status: {e}")
        raise


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
    search: Optional[str] = Query(None, description="Search query to filter files by name."),
    user_id: str = Depends(get_current_user_id)
):
    """List files from Google Drive"""
    try:
        service = GoogleDriveService(user_id)
        files = service.list_files(folder_id=folder_id, search_query=search)
        return {"files": files}
    except Exception as e:
        print(f"Error listing Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/files/recent")
async def list_recent_google_files(
    search: Optional[str] = Query(None, description="Search query to filter files by name."),
    user_id: str = Depends(get_current_user_id)
):
    """List recently accessed files from Google Drive"""
    try:
        service = GoogleDriveService(user_id)
        files = service.list_recent_files(search_query=search)
        return {"files": files}
    except Exception as e:
        print(f"Error listing recent Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/files/shared")
async def list_shared_google_files(
    search: Optional[str] = Query(None, description="Search query to filter files by name."),
    user_id: str = Depends(get_current_user_id)
):
    """List files shared with the user from Google Drive"""
    try:
        service = GoogleDriveService(user_id)
        files = service.list_shared_files(search_query=search)
        return {"files": files}
    except Exception as e:
        print(f"Error listing shared Google Drive files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/google/thumbnail")
async def get_google_drive_thumbnail(
    file_id: str = Query(..., description="Google Drive file ID"),
    authorization: Optional[str] = Header(None)
):
    """Proxy Google Drive thumbnail through backend to handle authentication"""
    # #region agent log
    import json
    from datetime import datetime
    log_path = r"c:\LegalAI\.cursor\debug.log"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"integrations.py:316","message":"Thumbnail endpoint called","data":{"file_id":file_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
    except: pass
    # #endregion
    
    try:
        # Get user ID from auth token
        user_id = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]
            try:
                # Create credentials object for get_current_user_id
                from fastapi.security import HTTPAuthorizationCredentials
                credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
                user_id = get_current_user_id(credentials)
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"integrations.py:298","message":"User authenticated","data":{"user_id":user_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
                except: pass
                # #endregion
            except Exception as auth_error:
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"integrations.py:305","message":"Auth failed","data":{"error":str(auth_error)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
                except: pass
                # #endregion
                pass  # If auth fails, we'll try without it
        
        if not user_id:
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"integrations.py:312","message":"No user_id, raising 401","data":{},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Check if Google Drive is connected for this user
        drive_service_check = GoogleDriveService(user_id)
        oauth_connection = drive_service_check._get_connection()
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"integrations.py:367","message":"Checking Google Drive connection","data":{"user_id":user_id,"has_connection":bool(oauth_connection),"file_id":file_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        
        # Get access token for this user
        service = GoogleDriveService(user_id)
        access_token = service.get_access_token()
        
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H3","location":"integrations.py:375","message":"Got access token","data":{"has_token":bool(access_token),"user_id":user_id,"file_id":file_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        
        if not access_token:
            raise HTTPException(status_code=401, detail="Failed to get access token")
        
        # Use Google Drive API to get file metadata with thumbnailLink
        drive_service = GoogleDriveService(user_id)
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H8","location":"integrations.py:380","message":"Initializing Google Drive service","data":{"user_id":user_id,"file_id":file_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        
        # Load credentials and build service (this returns True if successful)
        service_initialized = drive_service._load_credentials()
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H8","location":"integrations.py:383","message":"Service initialization result","data":{"initialized":service_initialized,"has_service":drive_service.service is not None,"user_id":user_id,"file_id":file_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        
        if not service_initialized or not drive_service.service:
            raise HTTPException(status_code=401, detail="Failed to initialize Google Drive service")
        
        try:
            # Get file metadata including thumbnailLink
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"integrations.py:390","message":"Calling Google Drive API files().get()","data":{"file_id":file_id,"user_id":user_id},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            
            file_metadata = drive_service.service.files().get(
                fileId=file_id,
                fields="thumbnailLink"
            ).execute()
            
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"integrations.py:397","message":"Google Drive API call successful","data":{"file_id":file_id,"has_metadata":bool(file_metadata)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            
            thumbnail_url = file_metadata.get('thumbnailLink')
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H5","location":"integrations.py:401","message":"Extracted thumbnailLink","data":{"file_id":file_id,"has_thumbnail_link":bool(thumbnail_url),"thumbnail_url":thumbnail_url[:100] if thumbnail_url else None},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            
            if not thumbnail_url:
                # No thumbnail available for this file type
                raise HTTPException(status_code=404, detail="Thumbnail not available for this file")
            
            # Add size parameter to thumbnail URL
            if 'sz=' not in thumbnail_url:
                thumbnail_url += '&sz=w500-h500' if '?' in thumbnail_url else '?sz=w500-h500'
            
            # Fetch the thumbnail image
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"integrations.py:411","message":"Fetching thumbnail from Google URL","data":{"file_id":file_id,"thumbnail_url":thumbnail_url[:150]},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    thumbnail_url,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0
                )
                
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"integrations.py:420","message":"Thumbnail fetch response","data":{"file_id":file_id,"status_code":response.status_code,"content_length":len(response.content),"content_type":response.headers.get("Content-Type")},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
                except: pass
                # #endregion
                
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to fetch thumbnail from Google Drive: {response.status_code}"
                    )
                
                # #region agent log
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H6","location":"integrations.py:428","message":"Returning thumbnail successfully","data":{"file_id":file_id,"content_length":len(response.content)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
                except: pass
                # #endregion
                
                return Response(
                    content=response.content,
                    media_type=response.headers.get("Content-Type", "image/jpeg"),
                    headers={
                        "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
                    }
                )
        except HTTPException:
            raise
        except Exception as api_error:
            # #region agent log
            try:
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"H4","location":"integrations.py:441","message":"Exception in Google Drive API call","data":{"file_id":file_id,"error_type":type(api_error).__name__,"error":str(api_error)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
            except: pass
            # #endregion
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get thumbnail: {str(api_error)}"
            )
    except HTTPException as e:
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"integrations.py:369","message":"HTTPException raised","data":{"status_code":e.status_code,"detail":str(e.detail)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        raise
    except Exception as e:
        # #region agent log
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"I","location":"integrations.py:376","message":"Exception in thumbnail endpoint","data":{"error_type":type(e).__name__,"error":str(e)},"timestamp":int(datetime.now().timestamp()*1000)}) + "\n")
        except: pass
        # #endregion
        print(f"Error fetching Google Drive thumbnail: {e}")
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

