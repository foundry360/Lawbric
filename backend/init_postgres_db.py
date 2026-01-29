#!/usr/bin/env python
"""
Initialize PostgreSQL database with all tables
Usage: python init_postgres_db.py
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import all models to ensure they're registered
# Import in order to avoid foreign key issues
from app.models.tenant import Tenant
from app.models.user import User
from app.models.case import Case, Document, DocumentChunk, Query
from app.models.audit import AuditLog, ImmutableAuditLog
# OAuth connection might have issues - import last
try:
    from app.models.oauth_connection import OAuthConnection
except Exception:
    pass  # Skip if there are issues
from app.core.database import Base

# PostgreSQL connection string
# Update this if your credentials are different
POSTGRES_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://legalai:legalai123@localhost:5432/legalai"
)

def init_database():
    """Create all tables in PostgreSQL"""
    print(f"Connecting to PostgreSQL: {POSTGRES_URL.split('@')[1] if '@' in POSTGRES_URL else 'localhost'}")
    
    engine = create_engine(POSTGRES_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"[OK] Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Create all tables
        print("\nCreating tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully!")
        
        # Create default tenant if it doesn't exist
        db = SessionLocal()
        try:
            # Check if default tenant exists
            result = db.execute(text("SELECT COUNT(*) FROM tenants WHERE slug = 'default'"))
            count = result.scalar()
            
            if count == 0:
                print("\nCreating default tenant...")
                db.execute(text("""
                    INSERT INTO tenants (id, name, slug, description, is_active, created_at)
                    VALUES (1, 'Default Tenant', 'default', 'Default tenant for existing data', true, NOW())
                """))
                db.commit()
                print("[OK] Default tenant created!")
            else:
                print("[OK] Default tenant already exists")
                
        except Exception as e:
            db.rollback()
            print(f"[WARNING] Could not create default tenant: {e}")
        finally:
            db.close()
        
        # List all created tables
        print("\nCreated tables:")
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            for table in tables:
                print(f"   - {table}")
        
        print(f"\n[OK] Database initialization complete!")
        print(f"\nYou can now connect to the database using:")
        print(f"   Host: localhost")
        print(f"   Port: 5432")
        print(f"   Database: legalai")
        print(f"   Username: legalai")
        print(f"   Password: legalai123")
        
    except Exception as e:
        print(f"\n[ERROR] Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    init_database()

