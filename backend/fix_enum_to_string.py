#!/usr/bin/env python
"""Convert role enum to string in PostgreSQL"""
from sqlalchemy import create_engine, text

POSTGRES_URL = "postgresql://legalai:legalai123@postgres:5432/legalai"

def fix_enum():
    engine = create_engine(POSTGRES_URL)
    conn = engine.connect()
    trans = conn.begin()
    
    try:
        # Convert enum column to VARCHAR
        print("Converting role enum to VARCHAR...")
        conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING role::text"))
        
        # Update values to lowercase to match Python enum values
        print("Updating role values to lowercase...")
        conn.execute(text("UPDATE users SET role = LOWER(role)"))
        
        trans.commit()
        print("Successfully converted role enum to VARCHAR with lowercase values")
        
        # Verify
        result = conn.execute(text("SELECT id, email, role FROM users"))
        users = result.fetchall()
        print(f"\nUsers in database:")
        for user in users:
            print(f"  {user[1]}: {user[2]}")
            
    except Exception as e:
        trans.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        engine.dispose()

if __name__ == "__main__":
    fix_enum()



