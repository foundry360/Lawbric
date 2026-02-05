#!/usr/bin/env python
"""
Create a super_admin user in PostgreSQL
Usage: python create_super_admin.py
"""

import sys
import os
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection string
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://legalai:legalai123@localhost:5432/legalai"
)

def create_super_admin(email: str, password: str, full_name: str = "Super Admin"):
    """Create a super_admin user directly in PostgreSQL"""
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
        
        # Hash password using bcrypt directly
        password_bytes = password.encode('utf-8')
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        hashed_password = hashed.decode('utf-8')
        
        # Create super_admin user
        result = db.execute(
            text("""
                INSERT INTO users (email, hashed_password, full_name, role, tenant_id, is_active, title)
                VALUES (:email, :hashed_password, :full_name, :role, :tenant_id, true, 'admin')
                RETURNING id
            """),
            {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "role": "super_admin",
                "tenant_id": tenant_id
            }
        )
        user_id = result.scalar()
        db.commit()
        
        print(f"[OK] Super admin user created successfully!")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Full Name: {full_name}")
        print(f"   Role: super_admin")
        print(f"   Tenant ID: {tenant_id}")
        print(f"\nYou can now login with:")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
        
        return True
        
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[ERROR] Failed to create super admin: {e}")
        traceback.print_exc()
        return False
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    email = "admin@superuser.com"
    password = "12345678"
    full_name = "Super Admin"
    
    create_super_admin(email, password, full_name)




