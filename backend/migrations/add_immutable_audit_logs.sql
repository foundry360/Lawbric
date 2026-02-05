-- Migration: Add immutable_audit_logs table
-- This table is append-only for Profile C (high-risk) actions
-- Each record includes a hash for integrity verification

CREATE TABLE IF NOT EXISTS immutable_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    case_id INTEGER,
    document_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id INTEGER,
    details TEXT,
    log_hash TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_immutable_audit_logs_user_id ON immutable_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS ix_immutable_audit_logs_case_id ON immutable_audit_logs(case_id);
CREATE INDEX IF NOT EXISTS ix_immutable_audit_logs_document_id ON immutable_audit_logs(document_id);
CREATE INDEX IF NOT EXISTS ix_immutable_audit_logs_action ON immutable_audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_immutable_audit_logs_log_hash ON immutable_audit_logs(log_hash);
CREATE INDEX IF NOT EXISTS ix_immutable_audit_logs_created_at ON immutable_audit_logs(created_at);

-- Note: SQLite doesn't support CHECK constraints to prevent UPDATE/DELETE
-- Append-only enforcement is handled at the application level in ImmutableLogger
-- For PostgreSQL, you would add triggers to prevent UPDATE/DELETE operations






