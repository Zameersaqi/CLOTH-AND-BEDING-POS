"""
Test Part 6: Editable Cart Prices, Customer Negotiations, and Master Catalog Isolation
"""

import unittest
import tempfile
from decimal import Decimal
from pathlib import Path
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories import CatalogRepository, SalesRepository, UserRepository, SettingsRepository
from app.services.sales_service import SalesService
from app.models.entities import User

class TestEditablePrices(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_prices.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)

        self.cat_repo = CatalogRepository(self.conn)
        self.sales_repo = SalesRepository(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.settings_repo = SettingsRepository(self.conn)
        self.sales_service = SalesService(self.sales_repo, self.user_repo, self.settings_repo)

        # Set max cashier discount to 15% and manager PIN to 1234
        self.settings_repo.set_setting("max_cashier_discount_percent", "15.0")
        self.settings_repo.set_setting("manager_pin", "1234")

        # Set a known price on a product
        prods = self.cat_repo.get_products()
        self.test_prod = prods[0]
        self.variant = self.test_prod.variants[0]
        self.cat_repo.update_variant_pricing_stock(
            self.variant.id,
            cost=Decimal("2000.00"),
            price=Decimal("3500.00"),
            stock=Decimal("10.000")
        )
        self.test_prod = self.cat_repo.get_product_by_id(self.test_prod.id)
        self.variant = self.test_prod.variants[0]

        self.cashier = User(
            id=2, username="cashier1", full_name="Cashier Staff",
            role="cashier", password_hash="", salt="", manager_pin=""
        )

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_cart_price_override_preserves_master_catalog_price(self):
        cart = []
        self.sales_service.add_to_cart(cart, self.test_prod, self.variant, Decimal("1.000"))
        item = cart[0]

        self.assertEqual(item.original_catalog_price, Decimal("3500.00"))
        self.assertEqual(item.transaction_price, Decimal("3500.00"))

        # Cashier reduces price to 3200 (within 15% limit: 300 / 3500 = 8.57%)
        success, msg = self.sales_service.update_cart_item_price(
            item=item,
            new_transaction_price=Decimal("3200.00"),
            current_user=self.cashier,
            override_reason="Bargained at counter"
        )
        self.assertTrue(success)
        self.assertEqual(item.transaction_price, Decimal("3200.00"))
        self.assertEqual(item.line_total, Decimal("3200.00"))
        self.assertTrue(item.is_price_overridden)

        # Complete sale
        ok, sale_msg, inv_no = self.sales_service.complete_checkout(
            cart=cart,
            customer_id=None,
            cashier_id=self.cashier.id,
            payment_method="Cash",
            tendered_cash=Decimal("3200.00")
        )
        self.assertTrue(ok)

        # CRITICAL VERIFICATION: Master catalog price in database MUST REMAIN 3500.00!
        fresh_prod = self.cat_repo.get_product_by_id(self.test_prod.id)
        self.assertEqual(fresh_prod.variants[0].selling_price, Decimal("3500.00"),
                         "CRITICAL: Master catalog price was erroneously altered by cart transaction!")

    def test_exceeding_discount_threshold_requires_manager_pin(self):
        cart = []
        self.sales_service.add_to_cart(cart, self.test_prod, self.variant, Decimal("1.000"))
        item = cart[0]

        # Cashier attempts a steep cut to 2500 (28.5% discount, exceeds 15% limit)
        success, msg = self.sales_service.update_cart_item_price(
            item=item,
            new_transaction_price=Decimal("2500.00"),
            current_user=self.cashier
        )
        self.assertFalse(success, "Excessive discount without Manager PIN must be rejected")
        self.assertIn("Manager PIN", msg)

        # Retry with invalid PIN
        success, msg = self.sales_service.update_cart_item_price(
            item=item,
            new_transaction_price=Decimal("2500.00"),
            current_user=self.cashier,
            manager_pin="9999"
        )
        self.assertFalse(success)

        # Retry with correct Manager PIN (1234)
        success, msg = self.sales_service.update_cart_item_price(
            item=item,
            new_transaction_price=Decimal("2500.00"),
            current_user=self.cashier,
            manager_pin="1234",
            override_reason="Manager approved customer special"
        )
        self.assertTrue(success, "Manager PIN must authorize price override")
        self.assertEqual(item.transaction_price, Decimal("2500.00"))

    def test_negative_prices_rejected(self):
        cart = []
        self.sales_service.add_to_cart(cart, self.test_prod, self.variant, Decimal("1.000"))
        item = cart[0]

        success, msg = self.sales_service.update_cart_item_price(
            item=item,
            new_transaction_price=Decimal("-500.00"),
            current_user=self.cashier
        )
        self.assertFalse(success)
        self.assertIn("negative", msg.lower())

if __name__ == "__main__":
    unittest.main()
