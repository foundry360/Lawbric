#!/usr/bin/env python
"""Drop the userrole enum type from PostgreSQL"""
from sqlalchemy import create_engine, text

POSTGRES_URL = "postgresql://legalai:legalai123@postgres:5432/legalai"

def drop_enum():
    engine = create_engine(POSTGRES_URL)
    conn = engine.connect()
    trans = conn.begin()
    
    try:
        # Check if enum type exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM pg_type WHERE typname = 'userrole'
            )
        """))
        exists = result.scalar()
        
        if exists:
            print("Dropping userrole enum type...")
            # First, we need to change the column type, then drop the enum
            conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING role::text"))
            conn.execute(text("DROP TYPE IF EXISTS userrole"))
            print("Enum type dropped successfully")
        else:
            print("Enum type does not exist")
        
        # Verify the column is now VARCHAR
        result = conn.execute(text("""
            SELECT data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'role'
        """))
        col_info = result.fetchone()
        if col_info:
            print(f"Column type: {col_info[0]} (max length: {col_info[1]})")
        
        trans.commit()
        print("Successfully converted role column to VARCHAR")
        
    except Exception as e:
        trans.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()
        engine.dispose()

if __name__ == "__main__":
    drop_enum()






