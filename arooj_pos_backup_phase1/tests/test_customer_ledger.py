"""
Test Customer Ledger, Credit Sales, and Payment Receipts
"""

import unittest
import tempfile
from decimal import Decimal
from pathlib import Path
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories import CatalogRepository, SalesRepository, CustomerRepository, UserRepository, SettingsRepository
from app.services.sales_service import SalesService
from app.models.entities import Customer

class TestCustomerLedger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_cust.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)

        self.cat_repo = CatalogRepository(self.conn)
        self.sales_repo = SalesRepository(self.conn)
        self.cust_repo = CustomerRepository(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.settings_repo = SettingsRepository(self.conn)
        self.sales_service = SalesService(self.sales_repo, self.user_repo, self.settings_repo)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_credit_sale_and_subsequent_payment(self):
        # 1. Create a credit customer
        cust = Customer(
            id=None,
            code="CUST-100",
            name="Zameer Textile Customer",
            phone="0300-9876543",
            credit_limit=Decimal("50000.00"),
            opening_balance=Decimal("0.00"),
            current_balance=Decimal("0.00"),
            notes="Regular credit account"
        )
        cust_id = self.cust_repo.create(cust)

        # 2. Add an item to cart: 2 bedsheet sets at 3000 each = 6000
        prods = self.cat_repo.get_products()
        p = prods[0]
        v = p.variants[0]
        self.cat_repo.update_variant_pricing_stock(v.id, Decimal("1800.00"), Decimal("3000.00"), Decimal("10.000"))
        p = self.cat_repo.get_product_by_id(p.id)
        v = p.variants[0]

        cart = []
        self.sales_service.add_to_cart(cart, p, v, Decimal("2.000"))

        # Customer pays only 2000 cash; 4000 remains due on credit
        ok, msg, inv_no = self.sales_service.complete_checkout(
            cart=cart,
            customer_id=cust_id,
            cashier_id=1,
            payment_method="Cash",
            tendered_cash=Decimal("2000.00")
        )
        self.assertTrue(ok)

        # Verify customer balance is now Rs. 4000.00
        fresh_cust = self.cust_repo.get_by_id(cust_id)
        self.assertEqual(fresh_cust.current_balance, Decimal("4000.00"))

        # 3. Later, customer comes to pay Rs. 3000 towards their balance
        new_bal = self.cust_repo.receive_payment(cust_id, Decimal("3000.00"), "Cash", "Partial account payment")
        self.assertEqual(new_bal, Decimal("1000.00"))

        # Verify customer ledger statement
        stmt = self.cust_repo.get_customer_statement(cust_id)
        self.assertGreaterEqual(len(stmt), 2)
        # Final running balance in ledger must equal 1000.00
        self.assertEqual(Decimal(str(stmt[-1]["running_balance"])), Decimal("1000.00"))

if __name__ == "__main__":
    unittest.main()
