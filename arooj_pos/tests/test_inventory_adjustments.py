"""
Tests for Phase 4 & Phase 5 Inventory Adjustments, Decimal Precision, Valuation, and Reorder Lists.
"""

import unittest
from decimal import Decimal
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.inventory_repository import InventoryRepository


class TestInventoryAdjustments(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.conn = self.db.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)
        self.catalog_repo = CatalogRepository(self.conn)
        self.inventory_repo = InventoryRepository(self.conn)

    def tearDown(self):
        self.db.close()

    def test_stock_adjustment_with_audit_reason_and_transaction_recording(self):
        # Create product with 20 stock
        prod_data = {
            "name": "Bedsheet Floral Print",
            "category_id": 1,
            "cost_price": Decimal("1500.00"),
            "sale_price": Decimal("2200.00"),
            "opening_stock": Decimal("20.000"),
            "sku": "ADJ-FLR-01",
            "is_active": 1
        }
        prod_id = self.catalog_repo.create_product(prod_data, user_id=1)
        variants = self.catalog_repo.get_variants_for_product(prod_id)
        variant_id = variants[0].id

        # Adjust stock down from 20 to 18 (2 units damaged in rain)
        success = self.inventory_repo.adjust_stock(
            product_id=prod_id,
            variant_id=variant_id,
            new_quantity=Decimal("18.000"),
            reason="Water damage during monsoon rain",
            user_id=1,
            transaction_type="damaged_spoilage"
        )
        self.assertTrue(success)

        # Verify variant stock updated
        cur = self.conn.cursor()
        cur.execute("SELECT stock_quantity FROM product_variants WHERE id = ?", (variant_id,))
        var_row = cur.fetchone()
        self.assertEqual(Decimal(str(var_row["stock_quantity"])), Decimal("18.000"))

        # Verify audit transaction record
        txns = self.inventory_repo.get_stock_transactions(product_id=prod_id)
        self.assertGreaterEqual(len(txns), 2)  # opening_stock + adjustment
        latest_txn = txns[0]
        self.assertEqual(latest_txn["transaction_type"], "damaged_spoilage")
        self.assertEqual(Decimal(str(latest_txn["quantity"])), Decimal("-2.000"))
        self.assertIn("Water damage", latest_txn["notes"])
        self.assertEqual(latest_txn["user_id"], 1)

    def test_fabric_meter_decimal_precision(self):
        # Fabric roll sold by length
        prod_data = {
            "name": "Boski Silk Fabric Unstitched",
            "category_id": 4,
            "product_nature": "fabric",
            "unit_id": 3,  # Meter
            "cost_price": Decimal("400.00"),
            "sale_price": Decimal("650.00"),
            "opening_stock": Decimal("100.750"),
            "sku": "FAB-BSK-01",
            "is_active": 1
        }
        prod_id = self.catalog_repo.create_product(prod_data, user_id=1)
        variants = self.catalog_repo.get_variants_for_product(prod_id)
        variant_id = variants[0].id

        # Adjust by 4.375 meters after exact measurement
        success = self.inventory_repo.adjust_stock(
            product_id=prod_id,
            variant_id=variant_id,
            new_quantity=Decimal("96.375"),
            reason="Physical roll remeasurement",
            user_id=1,
            transaction_type="count_correction"
        )
        self.assertTrue(success)

        cur = self.conn.cursor()
        cur.execute("SELECT stock_quantity FROM product_variants WHERE id = ?", (variant_id,))
        self.assertEqual(Decimal(str(cur.fetchone()["stock_quantity"])), Decimal("96.375"))

    def test_reorder_list_generator(self):
        # Create product with low stock
        prod_data = {
            "name": "Velvet Cushion Set",
            "category_id": 1,
            "cost_price": Decimal("800.00"),
            "sale_price": Decimal("1200.00"),
            "opening_stock": Decimal("2.000"),
            "min_stock_alert": Decimal("10.000"),
            "sku": "CSH-VLV-01",
            "is_active": 1
        }
        prod_id = self.catalog_repo.create_product(prod_data, user_id=1)

        reorder_items = self.inventory_repo.get_reorder_list()
        matching = [item for item in reorder_items if item["sku"] == "CSH-VLV-01"]
        self.assertEqual(len(matching), 1)
        item = matching[0]
        self.assertEqual(item["current_stock"], Decimal("2.000"))
        self.assertEqual(item["min_alert"], Decimal("10.000"))
        # Recommended order should bring stock up to double min alert (20 - 2 = 18)
        self.assertEqual(item["recommended_order"], Decimal("18.000"))

    def test_inventory_valuation_totals(self):
        # Create product with initial stock and pricing
        self.catalog_repo.create_product({
            "name": "Valuation Test Item",
            "category_id": 1,
            "cost_price": Decimal("1000.00"),
            "sale_price": Decimal("1500.00"),
            "opening_stock": Decimal("10.000"),
            "sku": "VAL-TEST-01",
            "is_active": 1
        }, user_id=1)

        items = self.inventory_repo.get_all_inventory_items()
        self.assertGreater(len(items), 0)
        total_units = sum(i["stock_quantity"] for i in items)
        total_cost = sum(i["cost_valuation"] for i in items)
        total_retail = sum(i["retail_valuation"] for i in items)

        self.assertGreater(total_units, Decimal("0"))
        self.assertGreater(total_cost, Decimal("0"))
        self.assertGreater(total_retail, total_cost)


if __name__ == "__main__":
    unittest.main()
