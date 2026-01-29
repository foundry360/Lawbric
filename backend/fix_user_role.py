#!/usr/bin/env python
"""Fix user role enum issue"""
import sys
from sqlalchemy import create_engine, text

POSTGRES_URL = "postgresql://legalai:legalai123@localhost:5432/legalai"

def fix_user_role():
    engine = create_engine(POSTGRES_URL)
    conn = engine.connect()
    
    try:
        # Check current role value
        result = conn.execute(text("SELECT id, email, role FROM users WHERE email = 'jgelsomino@foundry360.us'"))
        user = result.fetchone()
        if user:
            print(f"Current role: {user[2]} (type: {type(user[2])})")
        
        # PostgreSQL enum stores as uppercase, but we need lowercase to match Python enum
        # The enum in Python is: ADMIN = "admin", so the value should be "admin"
        # But PostgreSQL might have created it as uppercase
        
        # Let's check the enum type
        result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
            ORDER BY enumsortorder
        """))
        enum_values = [row[0] for row in result]
        print(f"PostgreSQL enum values: {enum_values}")
        
        # PostgreSQL enum expects uppercase, so update to 'ADMIN'
        conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE email = 'jgelsomino@foundry360.us'"))
        conn.commit()
        print("Updated user role to 'ADMIN' (uppercase to match PostgreSQL enum)")
        
        # Verify
        result = conn.execute(text("SELECT id, email, role FROM users WHERE email = 'jgelsomino@foundry360.us'"))
        user = result.fetchone()
        if user:
            print(f"Verified: User {user[0]} has role: {user[2]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        engine.dispose()

if __name__ == "__main__":
    fix_user_role()

