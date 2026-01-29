#!/usr/bin/env python
"""
Quick script to check a user's tenant assignment
Usage: python check_user_tenant.py <email>
"""

import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "sqlite:///./legalai.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_user_tenant(email: str):
    """Check user's tenant assignment"""
    db = SessionLocal()
    try:
        # Use raw SQL to avoid model import issues
        result = db.execute(
            text("SELECT id, email, full_name, role, tenant_id FROM users WHERE email = :email"),
            {"email": email}
        )
        user_row = result.fetchone()
        
        if not user_row:
            print(f"[ERROR] User with email '{email}' not found in local database")
            print("\nThis means the user hasn't been auto-created yet.")
            print("The user will be auto-created on their next API request.")
            return
        
        user_id, user_email, full_name, role, tenant_id = user_row
        
        print(f"[OK] User found:")
        print(f"   ID: {user_id}")
        print(f"   Email: {user_email}")
        print(f"   Full Name: {full_name}")
        print(f"   Role: {role}")
        print(f"   Tenant ID: {tenant_id}")
        
        if tenant_id:
            # Get tenant info
            tenant_result = db.execute(
                text("SELECT id, name, slug, description, is_active FROM tenants WHERE id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            tenant_row = tenant_result.fetchone()
            
            if tenant_row:
                tenant_id_db, tenant_name, tenant_slug, tenant_desc, tenant_active = tenant_row
                print(f"\n[OK] Tenant found:")
                print(f"   ID: {tenant_id_db}")
                print(f"   Name: {tenant_name}")
                print(f"   Slug: {tenant_slug}")
                print(f"   Description: {tenant_desc}")
                print(f"   Active: {tenant_active}")
            else:
                print(f"\n[WARNING] Tenant not found (tenant_id={tenant_id})")
            
            # Get cases for this tenant
            cases_result = db.execute(
                text("SELECT id, name FROM cases WHERE tenant_id = :tenant_id"),
                {"tenant_id": tenant_id}
            )
            cases = cases_result.fetchall()
            print(f"\n[INFO] Cases in this tenant: {len(cases)}")
            for case in cases:
                print(f"   - Case ID: {case[0]}, Name: {case[1]}")
        else:
            print(f"\n[WARNING] User has no tenant_id assigned")
            
    except Exception as e:
        import traceback
        print(f"[ERROR] Error: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_user_tenant.py <email>")
        print("\nExample: python check_user_tenant.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    check_user_tenant(email)
