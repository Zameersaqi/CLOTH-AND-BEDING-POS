"""
Tests for Phase 1 Product Management CRUD, SKU/Barcode Generation, and Variant Management.
"""

import unittest
from decimal import Decimal
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories.catalog_repository import CatalogRepository


class TestProductCrud(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.conn = self.db.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)
        self.repo = CatalogRepository(self.conn)

    def tearDown(self):
        self.db.close()

    def test_sku_and_barcode_generation(self):
        cat = self.repo.get_category_by_id(1)
        sku = self.repo.generate_unique_sku(category_id=1)
        self.assertTrue(sku.startswith(f"{cat.code}-"))
        self.assertFalse(self.repo.sku_exists(sku))

        barcode = self.repo.generate_unique_barcode()
        self.assertTrue(barcode.startswith("200"))
        self.assertEqual(len(barcode), 12)
        self.assertFalse(self.repo.barcode_exists(barcode))

    def test_create_standard_product_with_default_variant_and_opening_stock(self):
        prod_data = {
            "name": "Luxury Cotton Bedsheet",
            "name_urdu": " لگژری کاٹن بیڈ شیٹ",
            "category_id": 1,
            "subcategory_id": None,
            "product_nature": "standard",
            "unit_id": 1,
            "cost_price": Decimal("1800.00"),
            "sale_price": Decimal("2500.00"),
            "opening_stock": Decimal("15.000"),
            "min_stock_alert": Decimal("3.000"),
            "sku": "TEST-LUX-001",
            "barcode": "200999000111",
            "brand": "Arooj Luxury",
            "description": "High thread count cotton sheet",
            "is_active": 1
        }

        prod_id = self.repo.create_product(prod_data, user_id=1)
        self.assertIsNotNone(prod_id)

        # Verify product created
        prod = self.repo.get_product_by_id(prod_id)
        self.assertIsNotNone(prod)
        self.assertEqual(prod.name, "Luxury Cotton Bedsheet")
        self.assertEqual(prod.sale_price, Decimal("2500.00"))

        # Verify default variant created with stock
        variants = self.repo.get_variants_for_product(prod_id)
        self.assertEqual(len(variants), 1)
        default_var = variants[0]
        self.assertEqual(default_var.stock_quantity, Decimal("15.000"))
        self.assertEqual(default_var.sku, "TEST-LUX-001")
        self.assertEqual(default_var.barcode, "200999000111")

        # Verify opening stock transaction recorded
        cur = self.conn.cursor()
        cur.execute("SELECT transaction_type, quantity, unit_cost FROM stock_transactions WHERE product_id = ?", (prod_id,))
        txn = cur.fetchone()
        self.assertIsNotNone(txn)
        self.assertEqual(txn["transaction_type"], "opening_stock")
        self.assertEqual(Decimal(str(txn["quantity"])), Decimal("15.000"))
        self.assertEqual(Decimal(str(txn["unit_cost"])), Decimal("1800.00"))

    def test_update_product_preserves_stock_and_updates_prices(self):
        prod_data = {
            "name": "Single Cotton Bedcover",
            "category_id": 1,
            "cost_price": Decimal("1000.00"),
            "sale_price": Decimal("1400.00"),
            "opening_stock": Decimal("20.000"),
            "min_stock_alert": Decimal("5.000"),
            "sku": "SGL-COV-01",
            "barcode": "200888111222",
            "is_active": 1
        }
        prod_id = self.repo.create_product(prod_data, user_id=1)

        update_data = {
            "name": "Single Cotton Bedcover Deluxe",
            "name_urdu": "سنگل کاٹن بیڈ کور ڈیلکس",
            "category_id": 1,
            "subcategory_id": None,
            "product_nature": "standard",
            "unit_id": 1,
            "cost_price": Decimal("1100.00"),
            "sale_price": Decimal("1600.00"),
            "min_stock_alert": Decimal("6.000"),
            "sku": "SGL-COV-01",
            "barcode": "200888111222",
            "brand": "Arooj Home",
            "description": "Updated deluxe description",
            "is_active": 1
        }
        success = self.repo.update_product(prod_id, update_data)
        self.assertTrue(success)

        updated_prod = self.repo.get_product_by_id(prod_id)
        self.assertEqual(updated_prod.name, "Single Cotton Bedcover Deluxe")
        self.assertEqual(updated_prod.cost_price, Decimal("1100.00"))
        self.assertEqual(updated_prod.sale_price, Decimal("1600.00"))

        # Stock should still be 20
        variants = self.repo.get_variants_for_product(prod_id)
        self.assertEqual(variants[0].stock_quantity, Decimal("20.000"))

    def test_deactivate_and_activate_product(self):
        prod_data = {
            "name": "Winter Blanket Heavy",
            "category_id": 3,
            "cost_price": Decimal("3000.00"),
            "sale_price": Decimal("4500.00"),
            "opening_stock": Decimal("8.000"),
            "sku": "WNT-BLK-01",
            "barcode": "200777333444",
            "is_active": 1
        }
        prod_id = self.repo.create_product(prod_data, user_id=1)

        # Deactivate
        self.repo.deactivate_product(prod_id)
        prod = self.repo.get_product_by_id(prod_id)
        self.assertEqual(prod.is_active, 0)

        # Should not appear in active product list
        active_prods = self.repo.get_products(only_active=True)
        self.assertNotIn(prod_id, [p.id for p in active_prods])

        # Reactivate
        self.repo.activate_product(prod_id)
        prod = self.repo.get_product_by_id(prod_id)
        self.assertEqual(prod.is_active, 1)

    def test_variant_management_for_template_product(self):
        prod_data = {
            "name": "Silk Curtain Velvet",
            "category_id": 2,
            "cost_price": Decimal("2000.00"),
            "sale_price": Decimal("3200.00"),
            "is_template": 1,
            "product_nature": "variant",
            "sku": "VAR-SLK-01",
            "is_active": 1
        }
        prod_id = self.repo.create_product(prod_data, user_id=1)

        # Add Variant 1
        var1_data = {
            "product_id": prod_id,
            "sku": "VAR-SLK-01-RED",
            "barcode": "200111222333",
            "size": "7x4 Ft",
            "color": "Royal Maroon",
            "cost_price": Decimal("2100.00"),
            "sale_price": Decimal("3400.00"),
            "stock_quantity": Decimal("10.000"),
            "is_active": 1
        }
        var1_id = self.repo.create_variant(var1_data, user_id=1)
        self.assertIsNotNone(var1_id)

        # Add Variant 2
        var2_data = {
            "product_id": prod_id,
            "sku": "VAR-SLK-01-GLD",
            "barcode": "200111222444",
            "size": "7x4 Ft",
            "color": "Golden Ivory",
            "cost_price": Decimal("2200.00"),
            "sale_price": Decimal("3500.00"),
            "stock_quantity": Decimal("12.000"),
            "is_active": 1
        }
        var2_id = self.repo.create_variant(var2_data, user_id=1)
        self.assertIsNotNone(var2_id)

        variants = self.repo.get_variants_for_product(prod_id)
        self.assertEqual(len(variants), 2)

        # Update Variant 1
        self.repo.update_variant(var1_id, {
            "sku": "VAR-SLK-01-RED",
            "barcode": "200111222333",
            "size": "7x4 Ft",
            "color": "Dark Maroon",
            "design": "Embroidered",
            "fabric_type": "Velvet",
            "cost_price": Decimal("2150.00"),
            "sale_price": Decimal("3450.00"),
            "is_active": 1
        })

        cur = self.conn.cursor()
        cur.execute("SELECT color, design, selling_price FROM product_variants WHERE id = ?", (var1_id,))
        row = cur.fetchone()
        self.assertEqual(row["color"], "Dark Maroon")
        self.assertEqual(row["design"], "Embroidered")
        self.assertEqual(Decimal(str(row["selling_price"])), Decimal("3450.00"))


if __name__ == "__main__":
    unittest.main()
