"""
Test Sales Cart, Invoicing, Decimal Math, and Payments
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

class TestSalesCart(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_sales.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)

        self.cat_repo = CatalogRepository(self.conn)
        self.sales_repo = SalesRepository(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.settings_repo = SettingsRepository(self.conn)
        self.sales_service = SalesService(self.sales_repo, self.user_repo, self.settings_repo)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_invoice_number_generation(self):
        inv1 = self.sales_repo.generate_next_invoice_number()
        self.assertTrue(inv1.startswith("INV-"))
        self.assertTrue(inv1.endswith("-0001"))

    def test_cart_item_addition_and_totals(self):
        cart = []
        prods = self.cat_repo.get_products()
        p1 = prods[0]
        v1 = p1.variants[0]
        self.cat_repo.update_variant_pricing_stock(v1.id, Decimal("1000.00"), Decimal("1500.00"), Decimal("20.000"))
        # Refresh product with updated prices
        p1 = self.cat_repo.get_product_by_id(p1.id)
        v1 = p1.variants[0]

        # Add 2 units
        self.sales_service.add_to_cart(cart, p1, v1, Decimal("2.000"))
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0].quantity, Decimal("2.000"))
        self.assertEqual(cart[0].line_total, Decimal("3000.00"))

        # Add 1 more unit (increments quantity)
        self.sales_service.add_to_cart(cart, p1, v1, Decimal("1.000"))
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0].quantity, Decimal("3.000"))
        self.assertEqual(cart[0].line_total, Decimal("4500.00"))

        # Summary check with Rs. 200 bill discount
        summary = self.sales_service.calculate_cart_summary(cart, bill_discount=Decimal("200.00"))
        self.assertEqual(summary["subtotal"], Decimal("4500.00"))
        self.assertEqual(summary["discount_amount"], Decimal("200.00"))
        self.assertEqual(summary["grand_total"], Decimal("4300.00"))

    def test_complete_cash_checkout_deducts_stock(self):
        cart = []
        prods = self.cat_repo.get_products()
        p = prods[0]
        v = p.variants[0]
        self.cat_repo.update_variant_pricing_stock(v.id, Decimal("500.00"), Decimal("1000.00"), Decimal("15.000"))
        p = self.cat_repo.get_product_by_id(p.id)
        v = p.variants[0]

        self.sales_service.add_to_cart(cart, p, v, Decimal("3.000"))
        success, msg, inv_no = self.sales_service.complete_checkout(
            cart=cart,
            customer_id=None,
            cashier_id=1,
            payment_method="Cash",
            tendered_cash=Decimal("3500.00")
        )
        self.assertTrue(success)
        self.assertIn("Change: Rs. 500.00", msg)

        # Verify stock was deducted: 15.0 - 3.0 = 12.0
        updated_prod = self.cat_repo.get_product_by_id(p.id)
        self.assertEqual(updated_prod.variants[0].stock_quantity, Decimal("12.000"))

        # Verify sale record exists
        sale_data = self.sales_repo.get_sale_by_invoice(inv_no)
        self.assertIsNotNone(sale_data)
        self.assertEqual(float(sale_data["grand_total"]), 3000.0)
        self.assertEqual(len(sale_data["items"]), 1)

if __name__ == "__main__":
    unittest.main()
