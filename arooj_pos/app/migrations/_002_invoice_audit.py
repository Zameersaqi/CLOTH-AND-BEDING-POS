"""
Migration 002: Invoice Audit Logs and Revisions Support
"""

import sqlite3

def run_migration_002(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            sale_id INTEGER NOT NULL,
            old_subtotal REAL,
            new_subtotal REAL,
            old_discount REAL,
            new_discount REAL,
            old_grand_total REAL,
            new_grand_total REAL,
            changes_summary TEXT NOT NULL,
            edited_by TEXT,
            manager_pin_verified INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sale_id) REFERENCES sales (id) ON DELETE CASCADE
        );
    """)

    # Add is_revised and revision_count columns to sales table if not already present
    try:
        cursor.execute("ALTER TABLE sales ADD COLUMN is_revised INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE sales ADD COLUMN revision_count INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass

    conn.commit()
