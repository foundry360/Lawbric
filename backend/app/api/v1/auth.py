"""
Authentication endpoints - Pure JWT
Login and registration with JWT tokens
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.auth import get_current_user_and_tenant
from app.models.user import User, UserRole
from app.models.tenant import Tenant

router = APIRouter()
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"  # admin or user
    title: str = "attorney"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/password, returns JWT token"""
    try:
        user = db.query(User).filter(User.email == credentials.email).first()
    except Exception as e:
        import logging
        logging.error(f"Error querying user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    try:
        password_valid = verify_password(credentials.password, user.hashed_password)
    except Exception as e:
        import logging
        logging.error(f"Error verifying password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password verification error: {str(e)}"
        )
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create JWT token (sub must be a string)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register", response_model=TokenResponse)
async def register(user_data: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get or create default tenant
    default_tenant = db.query(Tenant).filter(Tenant.slug == 'default').first()
    if not default_tenant:
        default_tenant = Tenant(
            name='Default Tenant',
            slug='default',
            description='Default tenant',
            is_active=True
        )
        db.add(default_tenant)
        db.commit()
        db.refresh(default_tenant)
    
    # Map role string to enum
    role_map = {
        "admin": UserRole.ADMIN,
        "attorney": UserRole.ATTORNEY,
        "paralegal": UserRole.PARALEGAL
    }
    role = role_map.get(user_data.role.lower(), UserRole.PARALEGAL)
    
    # Create user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=role,
        tenant_id=default_tenant.id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Return JWT token (sub must be a string)
    token = create_access_token({"sub": str(new_user.id), "email": new_user.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    user_id, tenant_id = await get_current_user_and_tenant(credentials, db)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": str(user.role),  # Role is stored as string in database
        "title": user.title,  # Job title from database
        "tenant_id": tenant_id,
        "tenant_name": tenant.name if tenant else None
    }


@router.get("/tenant-info")
async def get_tenant_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user's tenant information"""
    try:
        user_id, tenant_id = await get_current_user_and_tenant(credentials, db)
        
        user = db.query(User).filter(User.id == user_id).first()
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Get case count for this tenant
        from app.models.case import Case as CaseModel
        case_count = db.query(CaseModel).filter(CaseModel.tenant_id == tenant_id).count()
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role": str(user.role),  # Role is stored as string in database
            },
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "description": tenant.description,
                "is_active": tenant.is_active,
            },
            "stats": {
                "case_count": case_count
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting tenant info: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tenant info: {str(e)}")
