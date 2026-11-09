"""
Test SQLite Online Backup, Integrity Check, and Database Restoration
"""

import unittest
import tempfile
from decimal import Decimal
from pathlib import Path
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.services.backup_service import BackupService
from app.repositories import CatalogRepository

class TestBackupRestore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "live_shop.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)
        self.backup_service = BackupService(self.db_mgr)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_backup_and_restore_cycle(self):
        # 1. Modify a product before backup
        cat_repo = CatalogRepository(self.conn)
        prods = cat_repo.get_products()
        test_prod = prods[0]
        v = test_prod.variants[0]
        cat_repo.update_variant_pricing_stock(v.id, Decimal("1000.00"), Decimal("2500.00"), Decimal("50.000"))

        # 2. Take online snapshot
        backup_file = self.backup_service.create_backup(Path(self.temp_dir.name))
        self.assertTrue(backup_file.exists())
        self.assertGreater(backup_file.stat().st_size, 0)

        # 3. Alter live database with a different price & stock
        cat_repo.update_variant_pricing_stock(v.id, Decimal("9999.00"), Decimal("9999.00"), Decimal("0.000"))
        altered_prod = cat_repo.get_product_by_id(test_prod.id)
        self.assertEqual(altered_prod.variants[0].selling_price, Decimal("9999.00"))

        # 4. Restore from backup
        ok = self.backup_service.restore_backup(backup_file)
        self.assertTrue(ok)

        # 5. Verify restored state matches snapshot
        restored_prod = cat_repo.get_product_by_id(test_prod.id)
        self.assertEqual(restored_prod.variants[0].selling_price, Decimal("2500.00"),
                         "Restored product price should match pre-backup state")
        self.assertEqual(restored_prod.variants[0].stock_quantity, Decimal("50.000"))

if __name__ == "__main__":
    unittest.main()
