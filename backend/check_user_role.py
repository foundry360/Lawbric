"""
Check user role in the database
"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

# Create database connection
engine = create_engine(settings.DATABASE_URL)

try:
    email = sys.argv[1] if len(sys.argv) > 1 else "jgelsomino@foundry360.us"
    
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, email, role, full_name, is_active, tenant_id FROM users WHERE email = :email"),
            {"email": email}
        )
        row = result.fetchone()
        
        if row:
            user_id, user_email, role, full_name, is_active, tenant_id = row
            print(f"User found: {user_email}")
            print(f"Role: {role}")
            print(f"Full Name: {full_name}")
            print(f"Is Active: {is_active}")
            print(f"Tenant ID: {tenant_id}")
            print(f"\nIs Super Admin: {role == 'super_admin'}")
        else:
            print(f"User with email '{email}' not found in database")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

