#!/usr/bin/env python
"""
Simple script to create a test user for development
Usage: python create_test_user.py <email> <password> [full_name] [role]
Example: python create_test_user.py admin@test.com password123 "Admin User" admin
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash

# Database connection
DATABASE_URL = "sqlite:///./legalai.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_user(email: str, password: str, full_name: str = None, role: str = "paralegal"):
    """Create a test user using raw SQL"""
    db = SessionLocal()
    try:
        # Check if user already exists using raw SQL
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
        
        # Get or create default tenant using raw SQL
        tenant_result = db.execute(
            text("SELECT id FROM tenants WHERE slug = 'default'")
        )
        tenant_row = tenant_result.fetchone()
        
        if not tenant_row:
            print("[INFO] Creating default tenant...")
            db.execute(
                text("""
                    INSERT INTO tenants (name, slug, description, is_active, created_at)
                    VALUES ('Default Tenant', 'default', 'Default tenant', 1, datetime('now'))
                """)
            )
            db.commit()
            tenant_result = db.execute(text("SELECT id FROM tenants WHERE slug = 'default'"))
            tenant_row = tenant_result.fetchone()
            print(f"[OK] Created default tenant (ID: {tenant_row[0]})")
        
        tenant_id = tenant_row[0]
        
        # Map role string to database value
        role_map = {
            "admin": "admin",
            "attorney": "attorney",
            "paralegal": "paralegal"
        }
        db_role = role_map.get(role.lower(), "paralegal")
        
        # Hash password
        hashed_password = get_password_hash(password)
        
        # Create user using raw SQL
        db.execute(
            text("""
                INSERT INTO users (email, hashed_password, full_name, role, tenant_id, is_active)
                VALUES (:email, :hashed_password, :full_name, :role, :tenant_id, 1)
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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python create_test_user.py <email> <password> [full_name] [role]")
        print("\nExample:")
        print("  python create_test_user.py admin@test.com password123")
        print("  python create_test_user.py admin@test.com password123 'Admin User' admin")
        print("\nRoles: admin, attorney, paralegal (default: paralegal)")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else None
    role = sys.argv[4] if len(sys.argv) > 4 else "paralegal"
    
    create_user(email, password, full_name, role)
