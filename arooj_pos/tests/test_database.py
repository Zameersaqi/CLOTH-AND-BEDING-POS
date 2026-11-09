"""
Test Database Initialization, Migrations, Foreign Keys, and ACID Transactions
"""

import unittest
import tempfile
import sqlite3
from pathlib import Path
from app.database import DatabaseManager
from app.migrations import apply_migrations

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_pos.db"
        self.db_mgr = DatabaseManager(self.db_path)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_migrations_create_all_tables(self):
        conn = self.db_mgr.get_connection()
        apply_migrations(conn)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}

        required_tables = {
            "schema_migrations", "categories", "subcategories", "units",
            "products", "product_variants", "fabric_rolls", "customers",
            "suppliers", "sales", "sale_items", "sale_payments",
            "held_sales", "stock_transactions", "customer_ledger",
            "supplier_ledger", "expenses", "users", "business_settings"
        }
        for tbl in required_tables:
            self.assertIn(tbl, tables, f"Expected table '{tbl}' was not created by migrations")

    def test_transaction_rollback_on_error(self):
        conn = self.db_mgr.get_connection()
        apply_migrations(conn)

        try:
            with self.db_mgr.transaction() as t_conn:
                cursor = t_conn.cursor()
                cursor.execute("INSERT INTO categories (code, name) VALUES ('TEST', 'Test Cat');")
                # Intentional error to trigger rollback
                cursor.execute("INSERT INTO nonexistent_table VALUES (1);")
        except Exception:
            pass

        # Verify rollback succeeded
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM categories WHERE code = 'TEST';")
        self.assertEqual(c.fetchone()[0], 0, "Transaction should have rolled back on error")

if __name__ == "__main__":
    unittest.main()
