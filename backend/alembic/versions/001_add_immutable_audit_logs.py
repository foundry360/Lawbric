"""add immutable audit logs

Revision ID: 001_add_immutable_audit_logs
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '001_add_immutable_audit_logs'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create immutable_audit_logs table
    op.create_table(
        'immutable_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('log_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_immutable_audit_logs_id'), 'immutable_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_immutable_audit_logs_user_id'), 'immutable_audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_immutable_audit_logs_case_id'), 'immutable_audit_logs', ['case_id'], unique=False)
    op.create_index(op.f('ix_immutable_audit_logs_document_id'), 'immutable_audit_logs', ['document_id'], unique=False)
    op.create_index(op.f('ix_immutable_audit_logs_action'), 'immutable_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_immutable_audit_logs_log_hash'), 'immutable_audit_logs', ['log_hash'], unique=False)
    op.create_index(op.f('ix_immutable_audit_logs_created_at'), 'immutable_audit_logs', ['created_at'], unique=False)
    
    # Note: SQLite doesn't support CHECK constraints to prevent UPDATE/DELETE
    # Append-only enforcement is handled at the application level
    # For PostgreSQL, you could add triggers to prevent UPDATE/DELETE:
    # CREATE OR REPLACE FUNCTION prevent_immutable_log_update()
    # RETURNS TRIGGER AS $$
    # BEGIN
    #     RAISE EXCEPTION 'Cannot update immutable audit logs';
    # END;
    # $$ LANGUAGE plpgsql;
    #
    # CREATE TRIGGER immutable_log_update_trigger
    # BEFORE UPDATE ON immutable_audit_logs
    # FOR EACH ROW EXECUTE FUNCTION prevent_immutable_log_update();
    #
    # CREATE TRIGGER immutable_log_delete_trigger
    # BEFORE DELETE ON immutable_audit_logs
    # FOR EACH ROW EXECUTE FUNCTION prevent_immutable_log_update();


def downgrade():
    op.drop_index(op.f('ix_immutable_audit_logs_created_at'), table_name='immutable_audit_logs')
    op.drop_index(op.f('ix_immutable_audit_logs_log_hash'), table_name='immutable_audit_logs')
    op.drop_index(op.f('ix_immutable_audit_logs_action'), table_name='immutable_audit_logs')
    op.drop_index(op.f('ix_immutable_audit_logs_document_id'), table_name='immutable_audit_logs')
    op.drop_index(op.f('ix_immutable_audit_logs_case_id'), table_name='immutable_audit_logs')
    op.drop_index(op.f('ix_immutable_audit_logs_user_id'), table_name='immutable_audit_logs')
    op.drop_index(op.f('ix_immutable_audit_logs_id'), table_name='immutable_audit_logs')
    op.drop_table('immutable_audit_logs')






