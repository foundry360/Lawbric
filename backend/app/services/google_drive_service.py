"""
Google Drive service for OAuth and file operations
"""

from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request
from app.core.config import settings
from app.core.supabase_db import get_oauth_connection, update_oauth_connection
import io
import json


class GoogleDriveService:
    """Service for interacting with Google Drive API"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.credentials: Optional[Credentials] = None
        self.service: Optional[Any] = None
    
    def _get_connection(self) -> Optional[Dict[str, Any]]:
        """Get OAuth connection from database"""
        return get_oauth_connection(self.user_id, 'google_drive')
    
    def _load_credentials(self) -> bool:
        """Load and refresh credentials from database"""
        connection = self._get_connection()
        if not connection:
            return False
        
        # Create credentials object
        creds_dict = {
            'token': connection['access_token'],
            'refresh_token': connection.get('refresh_token'),
            'token_uri': 'https://oauth2.googleapis.com/token',
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'scopes': self.SCOPES
        }
        
        self.credentials = Credentials.from_authorized_user_info(creds_dict)
        
        # Check if token is expired and refresh if needed
        # Use getattr to safely check attributes
        is_expired = getattr(self.credentials, 'expired', False)
        refresh_token = getattr(self.credentials, 'refresh_token', None)
        
        if is_expired and refresh_token:
            try:
                self.credentials.refresh(Request())
                # Update stored token - use expiry (datetime) instead of expires_in
                # NEVER access expires_in - it doesn't exist on Credentials object
                expires_at = None
                try:
                    expiry = getattr(self.credentials, 'expiry', None)
                    if expiry:
                        expires_at = expiry.isoformat()
                except (AttributeError, TypeError) as e:
                    print(f"Could not get expiry from credentials: {e}")
                    expires_at = None
                
                update_oauth_connection(
                    self.user_id,
                    'google_drive',
                    {
                        'access_token': self.credentials.token,
                        'token_expires_at': expires_at
                    }
                )
            except Exception as e:
                import traceback
                print(f"Error refreshing Google Drive token: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                return False
        
        # Build Drive service
        try:
            self.service = build('drive', 'v3', credentials=self.credentials)
            return True
        except Exception as e:
            print(f"Error building Drive service: {e}")
            return False
    
    def get_access_token(self) -> Optional[str]:
        """Get current access token, refreshing if necessary"""
        if not self._load_credentials():
            return None
        return self.credentials.token if self.credentials else None
    
    @staticmethod
    def get_authorization_url(redirect_uri: str) -> str:
        """Generate OAuth authorization URL"""
        # Ensure redirect_uri is properly formatted (no trailing spaces, etc.)
        redirect_uri = redirect_uri.strip()
        
        # Log for debugging
        print(f"Generating OAuth URL with redirect_uri: {redirect_uri}")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]  # Must match Google Cloud Console exactly
                }
            },
            scopes=GoogleDriveService.SCOPES,
            redirect_uri=redirect_uri
        )
        # Explicitly set redirect_uri again to ensure it's used
        flow.redirect_uri = redirect_uri
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        # Extract and log the redirect_uri from the generated URL
        from urllib.parse import urlparse, parse_qs, unquote
        parsed = urlparse(authorization_url)
        params = parse_qs(parsed.query)
        
        print("=" * 80)
        print("GOOGLE OAUTH URL GENERATION")
        print("=" * 80)
        print(f"Input redirect_uri: '{redirect_uri}'")
        if 'redirect_uri' in params:
            sent_redirect_uri = unquote(params['redirect_uri'][0])
            print(f"Redirect URI in generated URL: '{sent_redirect_uri}'")
            print(f"URIs match: {redirect_uri == sent_redirect_uri}")
            print(f"Length comparison - Input: {len(redirect_uri)}, Sent: {len(sent_redirect_uri)}")
            if redirect_uri != sent_redirect_uri:
                print("⚠️  WARNING: Redirect URI mismatch detected!")
                print(f"   Input:  '{redirect_uri}'")
                print(f"   Sent:   '{sent_redirect_uri}'")
        else:
            print("⚠️  WARNING: redirect_uri parameter not found in generated URL!")
        print(f"Full authorization URL: {authorization_url}")
        print("=" * 80)
        
        return authorization_url
    
    @staticmethod
    def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        redirect_uri = redirect_uri.strip()
        print(f"exchange_code_for_tokens called with redirect_uri: '{redirect_uri}'")
        print(f"Code length: {len(code)}")
        
        try:
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [redirect_uri]
                    }
                },
                scopes=GoogleDriveService.SCOPES,
                redirect_uri=redirect_uri
            )
            flow.redirect_uri = redirect_uri
            print(f"Fetching token with code (first 30 chars): {code[:30]}...")
            flow.fetch_token(code=code)
            print("Token fetch successful")
        except Exception as e:
            import traceback
            print("=" * 80)
            print("ERROR IN exchange_code_for_tokens")
            print("=" * 80)
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            print("=" * 80)
            raise
        
        credentials = flow.credentials
        return GoogleDriveService._extract_tokens_safely(credentials)
    
    @staticmethod
    def _extract_tokens_safely(credentials) -> Dict[str, Any]:
        """Safely extract tokens from credentials object without accessing expires_in"""
        if not credentials:
            raise Exception("No credentials returned from token exchange")
        
        # Safely access all attributes to avoid AttributeError
        try:
            access_token = getattr(credentials, 'token', None)
            if not access_token:
                raise Exception("No access token in credentials")
        except AttributeError as e:
            print(f"Error accessing token: {e}")
            raise Exception(f"Failed to get access token: {e}")
        
        # Handle expiration time - Google OAuth credentials use 'expiry' (datetime), not 'expires_in'
        # NEVER access expires_in directly - it doesn't exist on the Credentials object
        expires_at = None
        try:
            # Check for expiry attribute (datetime object) - NEVER use expires_in
            expiry = getattr(credentials, 'expiry', None)
            if expiry:
                expires_at = expiry.isoformat()
                print(f"Token expires at: {expires_at}")
            else:
                print("No expiry found in credentials (this is OK)")
        except (AttributeError, TypeError) as e:
            print(f"Error accessing expiry attribute: {e}")
            expires_at = None
        
        # Safely get refresh_token
        refresh_token = None
        try:
            refresh_token = getattr(credentials, 'refresh_token', None)
        except AttributeError:
            refresh_token = None
        
        print(f"Token exchange successful. Has refresh_token: {bool(refresh_token)}, expires_at: {expires_at}")
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_expires_at': expires_at
        }
    
    def list_files(self, folder_id: Optional[str] = None, page_size: int = 100, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files and folders from Google Drive"""
        if not self._load_credentials():
            raise Exception("Failed to load credentials or not connected")
        
        try:
            query = "trashed=false"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            else:
                query += " and 'root' in parents"
            
            # Add search query if provided
            if search_query and search_query.strip():
                # Escape single quotes in search query and wrap in quotes for exact matching
                escaped_query = search_query.replace("'", "\\'")
                query += f" and name contains '{escaped_query}'"
            
            results = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=query,
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, thumbnailLink, iconLink)",
                    pageToken=page_token,
                    orderBy="name"
                ).execute()
                
                files = response.get('files', [])
                results.extend(files)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            return results
        except Exception as e:
            print(f"Error listing Google Drive files: {e}")
            raise
    
    def list_recent_files(self, page_size: int = 100, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """List recently accessed files from Google Drive"""
        if not self._load_credentials():
            raise Exception("Failed to load credentials or not connected")
        
        try:
            query = "trashed=false"
            
            # Add search query if provided
            if search_query and search_query.strip():
                # Escape single quotes in search query and wrap in quotes for exact matching
                escaped_query = search_query.replace("'", "\\'")
                query += f" and name contains '{escaped_query}'"
            
            results = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=query,
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, thumbnailLink, iconLink, viewedByMeTime)",
                    pageToken=page_token,
                    orderBy="viewedByMeTime desc"
                ).execute()
                
                files = response.get('files', [])
                # Filter out files that have never been viewed
                files = [f for f in files if f.get('viewedByMeTime')]
                results.extend(files)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            return results[:page_size]  # Limit to page_size
        except Exception as e:
            print(f"Error listing recent Google Drive files: {e}")
            raise
    
    def list_shared_files(self, page_size: int = 100, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files shared with the user from Google Drive"""
        if not self._load_credentials():
            raise Exception("Failed to load credentials or not connected")
        
        try:
            query = "trashed=false and sharedWithMe=true"
            
            # Add search query if provided
            if search_query and search_query.strip():
                # Escape single quotes in search query and wrap in quotes for exact matching
                escaped_query = search_query.replace("'", "\\'")
                query += f" and name contains '{escaped_query}'"
            
            results = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=query,
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, webViewLink, thumbnailLink, iconLink)",
                    pageToken=page_token,
                    orderBy="modifiedTime desc"
                ).execute()
                
                files = response.get('files', [])
                results.extend(files)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
            
            return results
        except Exception as e:
            print(f"Error listing shared Google Drive files: {e}")
            raise
    
    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """Get metadata for a specific file"""
        if not self._load_credentials():
            raise Exception("Failed to load credentials or not connected")
        
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, size, modifiedTime, webViewLink, thumbnailLink, iconLink"
            ).execute()
            return file
        except Exception as e:
            print(f"Error getting file metadata: {e}")
            raise
    
    def download_file(self, file_id: str) -> Tuple[bytes, str]:
        """Download file content and return (content, filename)"""
        if not self._load_credentials():
            raise Exception("Failed to load credentials or not connected")
        
        try:
            # Get file metadata
            file_metadata = self.get_file_metadata(file_id)
            filename = file_metadata.get('name', 'unknown')
            mime_type = file_metadata.get('mimeType', '')
            
            # Check if this is a Google Workspace file (Docs, Sheets, Slides, etc.)
            # These need to be exported, not downloaded
            export_mime_types = {
                # Google Docs -> DOCX (primary), PDF (fallback)
                'application/vnd.google-apps.document': [
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/pdf'
                ],
                # Google Sheets -> XLSX (primary), PDF (fallback)
                'application/vnd.google-apps.spreadsheet': [
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'application/pdf'
                ],
                # Google Slides -> PPTX (primary), PDF (fallback)
                'application/vnd.google-apps.presentation': [
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'application/pdf'
                ],
                # Google Drawings -> PNG
                'application/vnd.google-apps.drawing': ['image/png'],
                # Google Forms -> PDF (may not be supported, fallback to HTML)
                'application/vnd.google-apps.form': ['application/pdf', 'text/html'],
                # Google Sites -> HTML (PDF not supported)
                'application/vnd.google-apps.site': ['text/html'],
                # Google Apps Script -> JSON
                'application/vnd.google-apps.script': ['application/vnd.google-apps.script+json'],
            }
            
            file_content = io.BytesIO()
            
            if mime_type in export_mime_types:
                # Use Export endpoint for Google Workspace files
                export_options = export_mime_types[mime_type]
                export_mime = None
                export_successful = False
                
                # Try each export format until one works
                for attempt_mime in export_options:
                    try:
                        # Export the file
                        request = self.service.files().export_media(fileId=file_id, mimeType=attempt_mime)
                        downloader = MediaIoBaseDownload(file_content, request)
                        
                        done = False
                        while not done:
                            status, done = downloader.next_chunk()
                        
                        export_mime = attempt_mime
                        export_successful = True
                        break  # Success, exit loop
                    except Exception as e:
                        error_str = str(e)
                        if 'not supported' in error_str.lower() or 'conversion' in error_str.lower():
                            # This export format isn't supported, try next one
                            file_content = io.BytesIO()  # Reset for next attempt
                            continue
                        else:
                            # Different error, re-raise
                            raise
                
                if not export_successful:
                    raise Exception(
                        f"File type '{mime_type}' does not support any of the available export formats. Supported formats: {', '.join(export_options)}. This file may not be downloadable."
                    )
                
                # Update filename extension based on export type
                if export_mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    if not filename.endswith('.docx'):
                        filename = filename.rsplit('.', 1)[0] + '.docx'
                elif export_mime == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                    if not filename.endswith('.xlsx'):
                        filename = filename.rsplit('.', 1)[0] + '.xlsx'
                elif export_mime == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
                    if not filename.endswith('.pptx'):
                        filename = filename.rsplit('.', 1)[0] + '.pptx'
                elif export_mime == 'image/png':
                    if not filename.endswith('.png'):
                        filename = filename.rsplit('.', 1)[0] + '.png'
                elif export_mime == 'application/pdf':
                    if not filename.endswith('.pdf'):
                        filename = filename.rsplit('.', 1)[0] + '.pdf'
                elif export_mime == 'text/html':
                    if not filename.endswith('.html'):
                        filename = filename.rsplit('.', 1)[0] + '.html'
            else:
                # Use regular download for binary files (PDF, images, DOCX, etc.)
                request = self.service.files().get_media(fileId=file_id)
                downloader = MediaIoBaseDownload(file_content, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            file_content.seek(0)
            return file_content.read(), filename
        except Exception as e:
            print(f"Error downloading file from Google Drive: {e}")
            raise

