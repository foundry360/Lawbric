"""add multi-tenant architecture

Revision ID: 002_add_multi_tenant
Revises: 001_add_immutable_audit_logs
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002_add_multi_tenant'
down_revision = '001_add_immutable_audit_logs'
branch_labels = None
depends_on = None


def upgrade():
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for tenants
    op.create_index(op.f('ix_tenants_id'), 'tenants', ['id'], unique=False)
    op.create_index(op.f('ix_tenants_name'), 'tenants', ['name'], unique=False)
    op.create_index(op.f('ix_tenants_slug'), 'tenants', ['slug'], unique=True)
    op.create_index(op.f('ix_tenants_domain'), 'tenants', ['domain'], unique=False)
    op.create_index(op.f('ix_tenants_is_active'), 'tenants', ['is_active'], unique=False)
    
    # Create a default tenant for existing data
    # We'll use a connection to insert the default tenant
    connection = op.get_bind()
    dialect_name = connection.dialect.name
    
    if dialect_name == 'postgresql':
        # PostgreSQL: use NOW() and reset sequence after insert
        connection.execute(
            sa.text("""
                INSERT INTO tenants (id, name, slug, description, is_active, created_at)
                VALUES (1, 'Default Tenant', 'default', 'Default tenant for existing data', true, NOW())
            """)
        )
        # Reset the PostgreSQL sequence to prevent ID conflicts
        # Find the actual sequence name dynamically
        seq_result = connection.execute(
            sa.text("SELECT pg_get_serial_sequence('tenants', 'id')")
        )
        sequence_name = seq_result.scalar()
        if sequence_name:
            # Extract just the sequence name (remove schema if present)
            if '.' in sequence_name:
                sequence_name = sequence_name.split('.')[-1]
            connection.execute(
                sa.text(f"SELECT setval('{sequence_name}', (SELECT MAX(id) FROM tenants))")
            )
        else:
            # Fallback: try the standard name
            try:
                connection.execute(
                    sa.text("SELECT setval('tenants_id_seq', (SELECT MAX(id) FROM tenants))")
                )
            except Exception:
                pass  # Sequence might not exist yet
    else:
        # SQLite: use datetime('now')
        connection.execute(
            sa.text("""
                INSERT INTO tenants (id, name, slug, description, is_active, created_at)
                VALUES (1, 'Default Tenant', 'default', 'Default tenant for existing data', 1, datetime('now'))
            """)
        )
    
    # Add tenant_id to users table
    op.add_column('users', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_users_tenant_id'), 'users', ['tenant_id'], unique=False)
    op.create_foreign_key('fk_users_tenant_id', 'users', 'tenants', ['tenant_id'], ['id'])
    
    # Set all existing users to default tenant
    connection.execute(
        sa.text("UPDATE users SET tenant_id = 1 WHERE tenant_id IS NULL")
    )
    
    # Make tenant_id NOT NULL after setting defaults
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # For now, we'll keep it nullable in SQLite but enforce NOT NULL at application level
    # For PostgreSQL, we would do: op.alter_column('users', 'tenant_id', nullable=False)
    
    # Add tenant_id to cases table
    op.add_column('cases', sa.Column('tenant_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_cases_tenant_id'), 'cases', ['tenant_id'], unique=False)
    op.create_foreign_key('fk_cases_tenant_id', 'cases', 'tenants', ['tenant_id'], ['id'])
    
    # Set all existing cases to default tenant
    connection.execute(
        sa.text("UPDATE cases SET tenant_id = 1 WHERE tenant_id IS NULL")
    )
    
    # Note: For production PostgreSQL, we would enforce NOT NULL constraints:
    # op.alter_column('users', 'tenant_id', nullable=False)
    # op.alter_column('cases', 'tenant_id', nullable=False)


def downgrade():
    # Remove tenant_id from cases
    op.drop_constraint('fk_cases_tenant_id', 'cases', type_='foreignkey')
    op.drop_index(op.f('ix_cases_tenant_id'), table_name='cases')
    op.drop_column('cases', 'tenant_id')
    
    # Remove tenant_id from users
    op.drop_constraint('fk_users_tenant_id', 'users', type_='foreignkey')
    op.drop_index(op.f('ix_users_tenant_id'), table_name='users')
    op.drop_column('users', 'tenant_id')
    
    # Drop tenants table
    op.drop_index(op.f('ix_tenants_is_active'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_domain'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_slug'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_name'), table_name='tenants')
    op.drop_index(op.f('ix_tenants_id'), table_name='tenants')
    op.drop_table('tenants')



