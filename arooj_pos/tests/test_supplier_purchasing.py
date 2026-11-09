"""
Tests for Phase 7 Supplier Management, Multi-line Purchasing, Stock Receiving, and Ledger Balances.
"""

import unittest
from decimal import Decimal
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories.supplier_repository import SupplierRepository
from app.repositories.catalog_repository import CatalogRepository


class TestSupplierPurchasing(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.conn = self.db.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)
        self.supplier_repo = SupplierRepository(self.conn)
        self.catalog_repo = CatalogRepository(self.conn)

    def tearDown(self):
        self.db.close()

    def test_supplier_creation_and_unique_code(self):
        code = self.supplier_repo.generate_unique_code()
        self.assertTrue(code.startswith("SUP-"))

        supp_id = self.supplier_repo.create({
            "code": code,
            "company_name": "Al-Karam Textile Mills",
            "contact_person": "Tariq Mahmood",
            "phone": "0300-9876543",
            "city": "Faisalabad",
            "address": "Millat Industrial Estate",
            "opening_balance": Decimal("50000.00"),
            "current_balance": Decimal("50000.00"),
            "is_active": 1
        })
        self.assertIsNotNone(supp_id)

        supp = self.supplier_repo.get_by_id(supp_id)
        self.assertEqual(supp.company_name, "Al-Karam Textile Mills")
        self.assertEqual(supp.current_balance, Decimal("50000.00"))

    def test_record_purchase_bill_with_stock_increment_and_ledger(self):
        # 1. Create a product with initial stock 10
        prod_data = {
            "name": "Bedsheet Bridal Set",
            "category_id": 1,
            "cost_price": Decimal("3000.00"),
            "sale_price": Decimal("4500.00"),
            "opening_stock": Decimal("10.000"),
            "sku": "BRD-SET-01",
            "is_active": 1
        }
        prod_id = self.catalog_repo.create_product(prod_data, user_id=1)
        variants = self.catalog_repo.get_variants_for_product(prod_id)
        variant_id = variants[0].id

        # 2. Create supplier
        supp_id = self.supplier_repo.create({
            "code": "SUP-TEST-01",
            "company_name": "Sitara Textiles",
            "current_balance": Decimal("0.00")
        })

        # 3. Record purchase bill: 20 units @ Rs. 3000 = Rs. 60,000. Paid Rs. 20,000. Due = Rs. 40,000.
        purchase_data = {
            "supplier_id": supp_id,
            "invoice_number": "SITARA-BILL-789",
            "total_amount": Decimal("60000.00"),
            "discount_amount": Decimal("0.00"),
            "net_amount": Decimal("60000.00"),
            "paid_amount": Decimal("20000.00"),
            "balance_amount": Decimal("40000.00"),
            "payment_status": "partial",
            "items": [
                {
                    "product_id": prod_id,
                    "variant_id": variant_id,
                    "quantity": Decimal("20.000"),
                    "unit_cost": Decimal("3000.00"),
                    "total_cost": Decimal("60000.00")
                }
            ],
            "notes": "Bulk bridal stock received"
        }

        purchase_id = self.supplier_repo.record_purchase(purchase_data, user_id=1)
        self.assertIsNotNone(purchase_id)

        # 4. Verify product stock incremented from 10 to 30
        cur = self.conn.cursor()
        cur.execute("SELECT stock_quantity FROM product_variants WHERE id = ?", (variant_id,))
        var_row = cur.fetchone()
        self.assertEqual(Decimal(str(var_row["stock_quantity"])), Decimal("30.000"))

        # 5. Verify stock transaction created for purchase
        cur.execute(
            "SELECT quantity, transaction_type, reference_id FROM stock_transactions WHERE product_id = ? AND transaction_type = 'purchase'",
            (prod_id,)
        )
        st_row = cur.fetchone()
        self.assertIsNotNone(st_row)
        self.assertEqual(Decimal(str(st_row["quantity"])), Decimal("20.000"))

        # 6. Verify supplier payable balance increased by Rs. 40,000
        supp = self.supplier_repo.get_by_id(supp_id)
        self.assertEqual(supp.current_balance, Decimal("40000.00"))

        # 7. Record subsequent payment of Rs. 25,000
        pay_success = self.supplier_repo.record_payment(
            supplier_id=supp_id,
            amount=Decimal("25000.00"),
            payment_method="bank",
            reference_no="CHQ-98012",
            notes="Partial bank transfer clearance",
            user_id=1
        )
        self.assertTrue(pay_success)

        # 8. Verify remaining balance is Rs. 15,000 (40,000 - 25,000)
        supp = self.supplier_repo.get_by_id(supp_id)
        self.assertEqual(supp.current_balance, Decimal("15000.00"))

        # 9. Verify supplier ledger entries
        ledger = self.supplier_repo.get_supplier_ledger(supp_id)
        self.assertEqual(len(ledger), 2)  # 1 purchase bill + 1 payment


if __name__ == "__main__":
    unittest.main()
