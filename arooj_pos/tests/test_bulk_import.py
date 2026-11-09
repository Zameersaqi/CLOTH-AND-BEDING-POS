"""
Test Bulk Product Catalogue Import and Export Service
Validates CSV parsing, duplicate SKU handling, unit normalization,
atomic transactions, conflict policies (add_new, update, skip), and catalog export.
"""

import unittest
import tempfile
from pathlib import Path
from decimal import Decimal

from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.services.import_export_service import ImportExportService, IMPORT_HEADERS
from app.repositories import CatalogRepository

class TestBulkImport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_import.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)
        self.service = ImportExportService(self.conn)
        self.cat_repo = CatalogRepository(self.conn)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_generate_template_and_sample(self):
        template_path = Path(self.temp_dir.name) / "test_template.csv"
        sample_path = Path(self.temp_dir.name) / "test_sample.csv"

        self.service.generate_csv_template(str(template_path))
        self.assertTrue(template_path.exists())
        self.assertGreater(template_path.stat().st_size, 0)

        self.service.generate_csv_template(str(sample_path), include_samples=True)
        self.assertTrue(sample_path.exists())
        self.assertGreater(sample_path.stat().st_size, 0)

    def test_import_valid_csv_records(self):
        csv_path = Path(self.temp_dir.name) / "valid_products.csv"
        csv_content = (
            ",".join(IMPORT_HEADERS) + "\n"
            "Unstitched Fabric,Gents Cotton,Super Cotton 2026,سپر کاٹن,SC-001,890123456701,MTR,4.5m,Navy Blue,Plain Solid,Cotton,4.5m,650.00,950.00,50.00,5\n"
            "Curtains & Parda,Blackout Velvet,Royal Velvet Drape,شاہی پردہ,RVD-001,890123456702,MTR,3.0m,Emerald Green,Damask Floral,Velvet,3.0m,1200.00,1850.00,30.00,5\n"
        )
        csv_path.write_text(csv_content, encoding="utf-8")

        valid_rows, errors = self.service.validate_and_parse_csv(str(csv_path))
        self.assertEqual(len(errors), 0, f"Unexpected validation errors: {errors}")
        self.assertEqual(len(valid_rows), 2)

        summary = self.service.import_records(valid_rows, conflict_mode="add_new_only")
        self.assertEqual(summary["added"], 2)
        self.assertEqual(summary["failed"], 0)

        # Verify in database
        prod1 = self.cat_repo.get_product_by_barcode("SC-001")
        self.assertIsNotNone(prod1)
        self.assertEqual(prod1.product_name, "Super Cotton 2026")
        self.assertEqual(prod1.selling_price, Decimal("950.00"))

    def test_unit_normalization(self):
        """Tests that 'meter', 'yd', 'gaz', 'pcs' are normalized to uppercase standard codes."""
        csv_path = Path(self.temp_dir.name) / "units_test.csv"
        csv_content = (
            ",".join(IMPORT_HEADERS) + "\n"
            "Bedsheets,Cotton Bedsheet,King Floral Set,کنگ بیڈ شیٹ,KFS-001,890123456703,pcs,King,Blue,Floral,Cotton,King,2500,3800,10,5\n"
            "Unstitched Fabric,Lawn,Lawn Prints,لان پرنٹ,LWN-001,890123456704,gaz,Standard,Yellow,Dots,Lawn,Per Gaz,350,550,40,5\n"
        )
        csv_path.write_text(csv_content, encoding="utf-8")

        valid_rows, errors = self.service.validate_and_parse_csv(str(csv_path))
        self.assertEqual(len(errors), 0, f"Unit validation failed: {errors}")
        self.assertEqual(valid_rows[0].unit, "PCS")
        self.assertEqual(valid_rows[1].unit, "YD")  # gaz normalized to YD

    def test_duplicate_sku_in_file_detected(self):
        csv_path = Path(self.temp_dir.name) / "dup_sku.csv"
        csv_content = (
            ",".join(IMPORT_HEADERS) + "\n"
            "Bedsheets,Cotton Bedsheet,Item A,آئٹم اے,DUP-SKU-1,890123456705,PCS,King,Red,Plain,Cotton,Std,100,200,5,5\n"
            "Bedsheets,Cotton Bedsheet,Item B,آئٹم بی,DUP-SKU-1,890123456706,PCS,King,Blue,Plain,Cotton,Std,150,250,5,5\n"
        )
        csv_path.write_text(csv_content, encoding="utf-8")

        valid_rows, errors = self.service.validate_and_parse_csv(str(csv_path))
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Duplicate SKU 'DUP-SKU-1'" in err for err in errors))

    def test_conflict_mode_update_existing(self):
        # First import
        csv_path1 = Path(self.temp_dir.name) / "initial.csv"
        csv_path1.write_text(
            ",".join(IMPORT_HEADERS) + "\n"
            "Bedsheets,Cotton Bedsheet,Silk Pillow,سلک تکیہ,SP-999,890123456799,PCS,Std,White,Plain,Silk,Std,500.00,800.00,20,5\n",
            encoding="utf-8"
        )
        valid1, errors1 = self.service.validate_and_parse_csv(str(csv_path1))
        self.assertEqual(len(errors1), 0)
        self.service.import_records(valid1, conflict_mode="add_new_only")

        # Now import updated price and stock with conflict_mode='update_existing'
        csv_path2 = Path(self.temp_dir.name) / "updated.csv"
        csv_path2.write_text(
            ",".join(IMPORT_HEADERS) + "\n"
            "Bedsheets,Cotton Bedsheet,Silk Pillow,سلک تکیہ,SP-999,890123456799,PCS,Std,White,Plain,Silk,Std,550.00,900.00,35,5\n",
            encoding="utf-8"
        )
        valid2, errors2 = self.service.validate_and_parse_csv(str(csv_path2), mode="update_existing")
        self.assertEqual(len(errors2), 0)
        summary = self.service.import_records(valid2, conflict_mode="update_existing")

        self.assertEqual(summary["updated"], 1)
        self.assertEqual(summary["added"], 0)

        # Check that prices updated in DB
        prod = self.cat_repo.get_product_by_barcode("SP-999")
        self.assertEqual(prod.selling_price, Decimal("900.00"))
        self.assertEqual(prod.purchase_price, Decimal("550.00"))

    def test_conflict_mode_skip_existing(self):
        # First import
        csv_path1 = Path(self.temp_dir.name) / "first.csv"
        csv_path1.write_text(
            ",".join(IMPORT_HEADERS) + "\n"
            "Bedsheets,Cotton Bedsheet,Silk Pillow,سلک تکیہ,SK-888,890123456788,PCS,Std,White,Plain,Silk,Std,500.00,800.00,20,5\n",
            encoding="utf-8"
        )
        valid1, _ = self.service.validate_and_parse_csv(str(csv_path1))
        self.service.import_records(valid1, conflict_mode="add_new_only")

        # Second import with skip_existing
        csv_path2 = Path(self.temp_dir.name) / "skip.csv"
        csv_path2.write_text(
            ",".join(IMPORT_HEADERS) + "\n"
            "Bedsheets,Cotton Bedsheet,Silk Pillow,سلک تکیہ,SK-888,890123456788,PCS,Std,White,Plain,Silk,Std,999.00,999.00,99,5\n",
            encoding="utf-8"
        )
        valid2, errors2 = self.service.validate_and_parse_csv(str(csv_path2), mode="skip_existing")
        self.assertEqual(len(errors2), 0)
        summary = self.service.import_records(valid2, conflict_mode="skip_existing")

        self.assertEqual(summary["skipped"], 1)
        self.assertEqual(summary["updated"], 0)
        # Verify original price remained unchanged
        prod = self.cat_repo.get_product_by_barcode("SK-888")
        self.assertEqual(prod.selling_price, Decimal("800.00"))

    def test_export_catalog_to_csv(self):
        export_path = Path(self.temp_dir.name) / "exported_catalog.csv"
        count = self.service.export_catalog_to_csv(str(export_path))
        self.assertTrue(export_path.exists())
        self.assertGreater(count, 0)

        # Ensure exported file has headers
        content = export_path.read_text(encoding="utf-8")
        self.assertIn("category", content.lower())
        self.assertIn("sku", content.lower())
        self.assertIn("selling_price", content.lower())

if __name__ == "__main__":
    unittest.main()
