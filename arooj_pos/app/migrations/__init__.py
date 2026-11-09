"""
Database migrations runner for Arooj POS
"""

import sqlite3
import logging
from typing import List

logger = logging.getLogger("arooj_pos.migrations")

def apply_migrations(conn: sqlite3.Connection):
    """Initializes schema and runs any pending migrations idempotently."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    cursor.execute("SELECT version FROM schema_migrations ORDER BY version ASC;")
    applied_versions = {row[0] for row in cursor.fetchall()}

    from app.migrations._001_initial_schema import run_migration_001
    from app.migrations._002_invoice_audit import run_migration_002

    if 1 not in applied_versions:
        logger.info("Applying migration 001: Initial schema setup")
        run_migration_001(conn)
        cursor.execute("INSERT INTO schema_migrations (version, name) VALUES (1, '001_initial_schema');")
        conn.commit()

    if 2 not in applied_versions:
        logger.info("Applying migration 002: Invoice revisions & audit logs")
        run_migration_002(conn)
        cursor.execute("INSERT INTO schema_migrations (version, name) VALUES (2, '002_invoice_audit');")
        conn.commit()
