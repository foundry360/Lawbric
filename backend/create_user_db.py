#!/usr/bin/env python
"""
Create a user directly in PostgreSQL database
Usage: python create_user_db.py <email> <password> [full_name] [role]
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash

# PostgreSQL connection string
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://legalai:legalai123@localhost:5432/legalai"
)

def create_user(email: str, password: str, full_name: str = None, role: str = "paralegal"):
    """Create a user directly in PostgreSQL"""
    engine = create_engine(POSTGRES_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Check if user already exists
        result = db.execute(
            text("SELECT id, email, full_name, role FROM users WHERE email = :email"),
            {"email": email}
        )
        existing = result.fetchone()
        
        if existing:
            print(f"[ERROR] User with email '{email}' already exists")
            print(f"   User ID: {existing[0]}")
            print(f"   Full Name: {existing[2]}")
            print(f"   Role: {existing[3]}")
            return False
        
        # Get default tenant
        tenant_result = db.execute(text("SELECT id FROM tenants WHERE slug = 'default'"))
        tenant_row = tenant_result.fetchone()
        
        if not tenant_row:
            print("[ERROR] Default tenant not found. Please run init_postgres_db.py first.")
            return False
        
        tenant_id = tenant_row[0]
        
        # Map role
        role_map = {
            "admin": "admin",
            "attorney": "attorney",
            "paralegal": "paralegal"
        }
        db_role = role_map.get(role.lower(), "paralegal")
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create user
        db.execute(
            text("""
                INSERT INTO users (email, hashed_password, full_name, role, tenant_id, is_active)
                VALUES (:email, :hashed_password, :full_name, :role, :tenant_id, true)
                RETURNING id
            """),
            {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name or email.split('@')[0],
                "role": db_role,
                "tenant_id": tenant_id
            }
        )
        db.commit()
        
        # Get the created user
        user_result = db.execute(
            text("SELECT id, email, full_name, role, tenant_id FROM users WHERE email = :email"),
            {"email": email}
        )
        new_user = user_result.fetchone()
        
        print(f"[OK] User created successfully!")
        print(f"   ID: {new_user[0]}")
        print(f"   Email: {new_user[1]}")
        print(f"   Full Name: {new_user[2]}")
        print(f"   Role: {new_user[3]}")
        print(f"   Tenant ID: {new_user[4]}")
        print(f"\nYou can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
        return True
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR] Failed to create user: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_user_db.py <email> <password> [full_name] [role]")
        print("\nExample:")
        print("  python create_user_db.py user@example.com password123")
        print("  python create_user_db.py user@example.com password123 'John Doe' admin")
        print("\nRoles: admin, attorney, paralegal (default: paralegal)")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else None
    role = sys.argv[4] if len(sys.argv) > 4 else "paralegal"
    
    create_user(email, password, full_name, role)



