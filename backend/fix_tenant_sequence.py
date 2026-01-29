#!/usr/bin/env python
"""
Fix PostgreSQL sequence for tenants table
This script resets the tenants_id_seq to the correct value to prevent ID conflicts.

Usage: python fix_tenant_sequence.py
"""
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# PostgreSQL connection string
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://legalai:legalai123@localhost:5432/legalai"
)

def fix_tenant_sequence():
    """Fix the PostgreSQL sequence for tenants table"""
    print(f"Connecting to PostgreSQL: {POSTGRES_URL.split('@')[1] if '@' in POSTGRES_URL else 'localhost'}")
    
    engine = create_engine(POSTGRES_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] Connected to PostgreSQL: {version.split(',')[0]}")
        
        db = SessionLocal()
        try:
            # Check if tenants table exists
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'tenants'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print("[ERROR] Tenants table does not exist. Please run migrations first.")
                return False
            
            # Get current max ID
            result = db.execute(text("SELECT MAX(id) FROM tenants"))
            max_id = result.scalar()
            
            if max_id is None:
                print("[INFO] No tenants found in database.")
                max_id = 0
            
            print(f"[INFO] Current maximum tenant ID: {max_id}")
            
            # Find the sequence name for tenants.id column
            # PostgreSQL sequences are typically named {table}_{column}_seq
            result = db.execute(text("""
                SELECT pg_get_serial_sequence('tenants', 'id')
            """))
            sequence_name = result.scalar()
            
            if not sequence_name:
                # Try to find it manually
                result = db.execute(text("""
                    SELECT sequence_name 
                    FROM information_schema.sequences 
                    WHERE sequence_name = 'tenants_id_seq'
                """))
                seq_row = result.fetchone()
                if seq_row:
                    sequence_name = seq_row[0]
                else:
                    print("[WARNING] Sequence for tenants.id not found. Creating it...")
                    # Create the sequence
                    db.execute(text("""
                        CREATE SEQUENCE IF NOT EXISTS tenants_id_seq OWNED BY tenants.id;
                        ALTER TABLE tenants ALTER COLUMN id SET DEFAULT nextval('tenants_id_seq');
                    """))
                    db.commit()
                    sequence_name = 'tenants_id_seq'
                    print("[OK] Sequence created.")
            
            # Extract just the sequence name (remove schema if present)
            if '.' in sequence_name:
                sequence_name = sequence_name.split('.')[-1]
            
            print(f"[INFO] Using sequence: {sequence_name}")
            
            # Ensure the sequence is owned by the column and default is set
            db.execute(text(f"""
                ALTER SEQUENCE {sequence_name} OWNED BY tenants.id;
                ALTER TABLE tenants ALTER COLUMN id SET DEFAULT nextval('{sequence_name}');
            """))
            db.commit()
            
            # Get current sequence value
            result = db.execute(text(f"SELECT last_value, is_called FROM {sequence_name}"))
            seq_info = result.fetchone()
            if seq_info:
                print(f"[INFO] Current sequence state: last_value={seq_info[0]}, is_called={seq_info[1]}")
            
            # Reset sequence to max_id (next value will be max_id + 1)
            # Use setval with is_called=true to set it so nextval will return max_id + 1
            # If max_id is 1, we want next to be 2, so we set it to 1 with is_called=true
            db.execute(text(f"""
                SELECT setval('{sequence_name}', {max_id}, true)
            """))
            db.commit()
            
            # Verify the sequence value by checking what nextval would return
            # We'll use a transaction that we can rollback
            db.begin()
            result = db.execute(text(f"SELECT nextval('{sequence_name}')"))
            next_val = result.scalar()
            db.rollback()  # Rollback the nextval since we just wanted to check
            
            print(f"[OK] Sequence reset successfully!")
            print(f"[INFO] Next auto-generated ID will be: {next_val}")
            
            if next_val != max_id + 1:
                print(f"[WARNING] Expected next ID to be {max_id + 1}, but got {next_val}")
                # Try alternative approach: set it to max_id with is_called=false
                print("[INFO] Trying alternative sequence reset method...")
                db.execute(text(f"""
                    SELECT setval('{sequence_name}', {max_id}, false)
                """))
                db.commit()
                db.begin()
                result = db.execute(text(f"SELECT nextval('{sequence_name}')"))
                next_val = result.scalar()
                db.rollback()
                print(f"[INFO] After alternative method, next ID will be: {next_val}")
                if next_val != max_id + 1:
                    return False
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"[ERROR] Failed to fix sequence: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            db.close()
        
    except Exception as e:
        print(f"\n[ERROR] Error connecting to database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        engine.dispose()

if __name__ == "__main__":
    success = fix_tenant_sequence()
    sys.exit(0 if success else 1)

