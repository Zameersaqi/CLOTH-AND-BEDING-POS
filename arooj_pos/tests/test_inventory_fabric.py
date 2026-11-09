"""
Test Fabric Length Tracking (Meters/Yards), Thaan Rolls, and Stock Deductions
"""

import unittest
import tempfile
from decimal import Decimal
from pathlib import Path
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories import CatalogRepository, SalesRepository, InventoryRepository, UserRepository, SettingsRepository
from app.services.sales_service import SalesService
from app.models.entities import FabricRoll

class TestInventoryFabric(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_fabric.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)

        self.cat_repo = CatalogRepository(self.conn)
        self.sales_repo = SalesRepository(self.conn)
        self.inv_repo = InventoryRepository(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.settings_repo = SettingsRepository(self.conn)
        self.sales_service = SalesService(self.sales_repo, self.user_repo, self.settings_repo)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_fabric_roll_length_deduction_on_sale(self):
        # Find a fabric product (e.g. Gents Fabric Thaan or Curtain Fabric)
        prods = self.cat_repo.get_products()
        fabric_prod = next((p for p in prods if p.is_fabric), None)
        self.assertIsNotNone(fabric_prod)

        var = fabric_prod.variants[0]
        self.cat_repo.update_variant_pricing_stock(var.id, Decimal("400.00"), Decimal("750.00"), Decimal("0.000"))

        # Register a new 45-meter Thaan (Roll)
        roll = FabricRoll(
            id=None,
            product_id=fabric_prod.id,
            variant_id=var.id,
            roll_number="TH-2026-001",
            initial_length=Decimal("45.000"),
            current_length=Decimal("45.000"),
            unit_name="Meter",
            cost_per_unit=Decimal("400.00"),
            notes="Initial roll from textile mill"
        )
        roll_id = self.inv_repo.add_fabric_roll(roll)
        roll.id = roll_id

        # Verify initial roll length
        rolls = self.inv_repo.get_fabric_rolls_for_product(fabric_prod.id)
        self.assertEqual(len(rolls), 1)
        self.assertEqual(rolls[0].current_length, Decimal("45.000"))

        # Customer buys 4.5 meters cut from this thaan
        cart = []
        fabric_prod = self.cat_repo.get_product_by_id(fabric_prod.id)
        var = fabric_prod.variants[0]
        self.sales_service.add_to_cart(cart, fabric_prod, var, Decimal("4.500"), fabric_roll=roll)

        self.assertEqual(cart[0].line_total, Decimal("3375.00"))  # 4.5 * 750 = 3375.00

        # Complete Sale
        ok, msg, inv_no = self.sales_service.complete_checkout(
            cart=cart,
            customer_id=None,
            cashier_id=1,
            payment_method="Cash",
            tendered_cash=Decimal("3500.00")
        )
        self.assertTrue(ok)

        # Verify remaining length on thaan: 45.000 - 4.500 = 40.500 meters
        updated_rolls = self.inv_repo.get_fabric_rolls_for_product(fabric_prod.id)
        self.assertEqual(updated_rolls[0].current_length, Decimal("40.500"),
                         "Remaining length of fabric roll must be exactly 40.500 meters")

if __name__ == "__main__":
    unittest.main()
