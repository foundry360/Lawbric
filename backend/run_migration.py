"""
Simple script to run the multi-tenant migration
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import engine, SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.models.case import Case
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the multi-tenant migration"""
    db = SessionLocal()
    
    try:
        logger.info("Starting multi-tenant migration...")
        
        # Check if tenants table already exists
        result = db.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='tenants'
        """))
        table_exists = result.fetchone() is not None
        
        if table_exists:
            logger.info("Tenants table already exists. Checking if migration is needed...")
            # Check if tenant_id columns exist
            result = db.execute(text("PRAGMA table_info(users)"))
            user_columns = [row[1] for row in result.fetchall()]
            
            if 'tenant_id' in user_columns:
                logger.info("Migration already applied. Skipping.")
                return
            else:
                logger.info("Tenants table exists but columns missing. Adding columns...")
        else:
            # Create tenants table
            logger.info("Creating tenants table...")
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    slug VARCHAR NOT NULL UNIQUE,
                    description TEXT,
                    domain VARCHAR,
                    logo_url VARCHAR,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME
                )
            """))
            
            # Create indexes
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_tenants_id ON tenants(id)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_tenants_name ON tenants(name)"))
            db.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tenants_slug ON tenants(slug)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_tenants_domain ON tenants(domain)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_tenants_is_active ON tenants(is_active)"))
            
            db.commit()
            logger.info("Tenants table created.")
        
        # Create default tenant
        logger.info("Creating default tenant...")
        result = db.execute(text("SELECT COUNT(*) FROM tenants"))
        tenant_count = result.fetchone()[0]
        
        if tenant_count == 0:
            db.execute(text("""
                INSERT INTO tenants (id, name, slug, description, is_active, created_at)
                VALUES (1, 'Default Tenant', 'default', 'Default tenant for existing data', 1, datetime('now'))
            """))
            db.commit()
            logger.info("Default tenant created.")
        else:
            logger.info("Default tenant already exists.")
        
        # Add tenant_id to users table
        logger.info("Adding tenant_id to users table...")
        try:
            db.execute(text("ALTER TABLE users ADD COLUMN tenant_id INTEGER"))
            db.commit()
            logger.info("tenant_id column added to users table.")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("tenant_id column already exists in users table.")
            else:
                raise
        
        # Create index and foreign key for users.tenant_id
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users(tenant_id)"))
            # SQLite doesn't support adding foreign keys via ALTER TABLE, so we'll skip it
            # The relationship is enforced at the application level
            db.commit()
        except Exception as e:
            logger.warning(f"Could not create index/foreign key: {e}")
        
        # Set all existing users to default tenant
        logger.info("Assigning existing users to default tenant...")
        db.execute(text("UPDATE users SET tenant_id = 1 WHERE tenant_id IS NULL"))
        db.commit()
        logger.info("Users assigned to default tenant.")
        
        # Add tenant_id to cases table
        logger.info("Adding tenant_id to cases table...")
        try:
            db.execute(text("ALTER TABLE cases ADD COLUMN tenant_id INTEGER"))
            db.commit()
            logger.info("tenant_id column added to cases table.")
        except Exception as e:
            if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                logger.info("tenant_id column already exists in cases table.")
            else:
                raise
        
        # Create index and foreign key for cases.tenant_id
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_cases_tenant_id ON cases(tenant_id)"))
            db.commit()
        except Exception as e:
            logger.warning(f"Could not create index: {e}")
        
        # Set all existing cases to default tenant
        logger.info("Assigning existing cases to default tenant...")
        db.execute(text("UPDATE cases SET tenant_id = 1 WHERE tenant_id IS NULL"))
        db.commit()
        logger.info("Cases assigned to default tenant.")
        
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()



