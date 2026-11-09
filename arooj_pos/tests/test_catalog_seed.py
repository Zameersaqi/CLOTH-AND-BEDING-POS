"""
Test Catalog Seeding, Pakistani Categories, and Idempotency
"""

import unittest
import tempfile
from pathlib import Path
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories.catalog_repository import CatalogRepository

class TestCatalogSeed(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_seed.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_initial_catalog_seeded_with_all_categories(self):
        seed_database(self.conn)
        repo = CatalogRepository(self.conn)
        categories = repo.get_categories()

        cat_codes = {c.code for c in categories}
        expected_cats = {
            "RAZAI", "KAMBAL", "AC_KAMBAL", "KHAIS", "BEDSHEETS",
            "BRIDAL_SETS", "CUSHIONS", "KAMBAL_SETS", "ABAYAS",
            "LADIES_STITCHED", "LADIES_UNSTITCHED", "GENTS_CLOTH",
            "CURTAINS", "SCARVES", "STALLER", "ADDITIONAL"
        }
        for exp in expected_cats:
            self.assertIn(exp, cat_codes, f"Required category '{exp}' missing from preloaded catalog")

        # Verify products exist
        prods = repo.get_products()
        self.assertGreater(len(prods), 15, "Expected preloaded editable product templates")

    def test_seeding_is_idempotent(self):
        # Run seed first time
        seed_database(self.conn)
        repo = CatalogRepository(self.conn)
        count_first = len(repo.get_categories())
        prod_count_first = len(repo.get_products())

        # Run seed second time
        seed_database(self.conn)
        count_second = len(repo.get_categories())
        prod_count_second = len(repo.get_products())

        self.assertEqual(count_first, count_second, "Repeated seeding must not duplicate categories")
        self.assertEqual(prod_count_first, prod_count_second, "Repeated seeding must not duplicate products")

if __name__ == "__main__":
    unittest.main()
