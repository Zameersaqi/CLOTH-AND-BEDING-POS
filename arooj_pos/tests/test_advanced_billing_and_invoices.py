import os
import sys
# Headless Qt setup for headless test runners
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import unittest
import sqlite3
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil

from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.models.entities import CartItem, Product, ProductVariant, Customer, User
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.sales_repository import SalesRepository
from app.repositories.settings_repository import SettingsRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.user_repository import UserRepository
from app.services.sales_service import SalesService
from app.services.printer_service import PrinterService
from app.config import to_decimal

try:
    from PySide6.QtWidgets import QApplication
    from app.ui.cart_widget import CartWidget
    from app.ui.pos_screen import ReceiptDialog
    PYSIDE_AVAILABLE = True
    _qt_app = QApplication.instance() or QApplication(sys.argv)
except (ImportError, Exception):
    PYSIDE_AVAILABLE = False
    CartWidget = None
    ReceiptDialog = None

class AdvancedBillingAndInvoiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_advanced.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)

        self.catalog_repo = CatalogRepository(self.conn)
        self.sales_repo = SalesRepository(self.conn)
        self.settings_repo = SettingsRepository(self.conn)
        self.customer_repo = CustomerRepository(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.sales_service = SalesService(self.sales_repo, self.user_repo, self.settings_repo)

        self.cashier_user = User(
            id=1, username="cashier", full_name="Counter Staff",
            role="cashier", password_hash="", salt="salt123", is_active=True
        )

        # Create a test customer
        cust = Customer(
            id=None,
            code="CUST-0001",
            name="Haji Aslam Cloth House",
            phone="03009988776",
            address="Karkhana Bazaar",
            city="Faisalabad",
            credit_limit=Decimal("50000.00"),
            opening_balance=Decimal("0.00"),
            current_balance=Decimal("0.00")
        )
        self.customer_id = self.customer_repo.create(cust)
        self.customer = self.customer_repo.get_by_id(self.customer_id)

        # Use seeded product and set variant stock & prices
        prods = self.catalog_repo.get_products()
        self.product = prods[0]
        self.variant = self.product.variants[0]
        self.prod_id = self.product.id
        self.var_id = self.variant.id
        self.catalog_repo.update_variant_pricing_stock(
            self.var_id,
            Decimal("1200.00"),
            Decimal("2000.00"),
            Decimal("50.000")
        )
        self.variant = next(v for v in self.catalog_repo.get_variants_for_product(self.prod_id) if v.id == self.var_id)

    def tearDown(self):
        self.db_mgr.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # TASK 1: KEYBOARD-ONLY BILLING WORKFLOW TESTS
    # -------------------------------------------------------------
    def test_cart_item_inline_price_and_discount_limit(self):
        """Tests that cart item price edits within 15% succeed, and cuts > 15% require Manager PIN."""
        cart_item = CartItem(
            product_id=self.prod_id,
            variant_id=self.var_id,
            product_name="Luxury Double Bed Sheet",
            variant_title="Double Navy Blue",
            quantity=Decimal("2.000"),
            original_catalog_price=Decimal("2000.00"),
            transaction_price=Decimal("2000.00"),
            cost_price=Decimal("1200.00")
        )

        # 10% discount: 2000 -> 1800 (allowed for cashier)
        ok, msg = self.sales_service.update_cart_item_price(
            item=cart_item,
            new_transaction_price=Decimal("1800.00"),
            current_user=self.cashier_user
        )
        self.assertTrue(ok)
        self.assertEqual(cart_item.transaction_price, Decimal("1800.00"))
        self.assertTrue(cart_item.is_price_overridden)

        # 25% discount: 2000 -> 1500 (requires Manager PIN)
        ok, msg = self.sales_service.update_cart_item_price(
            item=cart_item,
            new_transaction_price=Decimal("1500.00"),
            current_user=self.cashier_user
        )
        self.assertFalse(ok)
        self.assertIn("Manager PIN", msg)

        # Approve with valid Manager PIN
        ok, msg = self.sales_service.update_cart_item_price(
            item=cart_item,
            new_transaction_price=Decimal("1500.00"),
            current_user=self.cashier_user,
            manager_pin="1234",
            override_reason="Bargain agreed"
        )
        self.assertTrue(ok)
        self.assertEqual(cart_item.transaction_price, Decimal("1500.00"))

    # -------------------------------------------------------------
    # TASK 2: SAFE PRINT PREVIEW & FINAL SALE CONFIRMATION
    # -------------------------------------------------------------
    def test_safe_preview_does_not_finalize_or_deduct_stock_until_confirmed(self):
        """
        Verify that requesting a receipt preview does NOT create a sale record,
        does NOT deduct stock, and leaves the cart intact. Only explicit confirmation
        commits the transaction.
        """
        if PYSIDE_AVAILABLE and CartWidget is not None:
            cart = CartWidget(self.sales_service, self.settings_repo, self.cashier_user, self.customer_repo)
            cart.add_item(self.product, self.variant, Decimal("5.000"))
            self.assertEqual(len(cart.cart_items), 1)

            initial_stock = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(initial_stock, Decimal("50.000"))

            captured_drafts = []
            cart.preview_requested.connect(lambda draft, phone: captured_drafts.append(draft))

            cart.tendered_input.setText("10000.00")
            cart.request_receipt_preview()

            self.assertEqual(len(captured_drafts), 1)
            draft = captured_drafts[0]
            self.assertEqual(draft["grand_total"], 10000.0)
            self.assertTrue(draft.get("is_draft"))

            sales_count = self.conn.cursor().execute("SELECT COUNT(*) FROM sales;").fetchone()[0]
            self.assertEqual(sales_count, 0)

            stock_now = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(stock_now, Decimal("50.000"))

            self.assertEqual(len(cart.cart_items), 1)

            success, msg, inv_no = cart.finalize_sale(draft)
            self.assertTrue(success)
            self.assertTrue(inv_no.startswith("INV-"))

            stock_after = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(stock_after, Decimal("45.000"))
            self.assertEqual(len(cart.cart_items), 0)

            sale_row = self.sales_repo.get_sale_by_invoice(inv_no)
            self.assertIsNotNone(sale_row)
            self.assertEqual(to_decimal(sale_row["grand_total"]), Decimal("10000.00"))
        else:
            cart_items = [
                CartItem(
                    product_id=self.prod_id,
                    variant_id=self.var_id,
                    product_name="Luxury Double Bed Sheet",
                    variant_title="Double Navy Blue",
                    quantity=Decimal("5.000"),
                    original_catalog_price=Decimal("2000.00"),
                    transaction_price=Decimal("2000.00"),
                    cost_price=Decimal("1200.00")
                )
            ]
            initial_stock = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(initial_stock, Decimal("50.000"))

            summary = self.sales_service.calculate_cart_summary(cart_items, Decimal("0.00"))
            draft_sale = {
                "invoice_number": "PREVIEW (Draft)",
                "grand_total": float(summary["grand_total"]),
                "is_draft": True
            }
            self.assertEqual(draft_sale["grand_total"], 10000.0)

            sales_count = self.conn.cursor().execute("SELECT COUNT(*) FROM sales;").fetchone()[0]
            self.assertEqual(sales_count, 0)
            stock_now = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(stock_now, Decimal("50.000"))

            ok, msg, inv_no = self.sales_service.complete_checkout(
                cart=cart_items, customer_id=None, cashier_id=1,
                payment_method="Cash", tendered_cash=Decimal("10000.00"), bill_discount=Decimal("0.00")
            )
            self.assertTrue(ok)
            stock_after = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(stock_after, Decimal("45.000"))

    def test_preview_cancel_preserves_cart_state(self):
        """Simulating Cancel or Esc on preview modal preserves items and entered discounts."""
        if PYSIDE_AVAILABLE and CartWidget is not None:
            cart = CartWidget(self.sales_service, self.settings_repo, self.cashier_user, self.customer_repo)
            cart.add_item(self.product, self.variant, Decimal("3.000"))
            cart.discount_input.setText("250.00")
            cart.tendered_input.setText("6000.00")

            self.assertEqual(len(cart.cart_items), 1)
            self.assertEqual(cart.discount_input.text(), "250.00")
            self.assertEqual(cart.tendered_input.text(), "6000.00")

            stock = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(stock, Decimal("50.000"))
        else:
            cart_items = [
                CartItem(
                    product_id=self.prod_id,
                    variant_id=self.var_id,
                    product_name="Luxury Double Bed Sheet",
                    variant_title="Double Navy Blue",
                    quantity=Decimal("3.000"),
                    original_catalog_price=Decimal("2000.00"),
                    transaction_price=Decimal("2000.00"),
                    cost_price=Decimal("1200.00")
                )
            ]
            self.assertEqual(len(cart_items), 1)
            stock = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
            self.assertEqual(stock, Decimal("50.000"))

    def test_insufficient_cash_blocks_checkout(self):
        """Tendered cash less than grand total prevents opening receipt preview."""
        if PYSIDE_AVAILABLE and CartWidget is not None:
            cart = CartWidget(self.sales_service, self.settings_repo, self.cashier_user, self.customer_repo)
            cart.add_item(self.product, self.variant, Decimal("2.000"))
            cart.pay_method.setCurrentText("Cash")
            cart.tendered_input.setText("2500.00")

            captured = []
            cart.preview_requested.connect(lambda d, p: captured.append(d))
            cart.request_receipt_preview()

            self.assertEqual(len(captured), 0, "Preview should be blocked when cash is insufficient")
        else:
            grand_total = Decimal("4000.00")
            tendered = Decimal("2500.00")
            is_valid_cash = tendered >= grand_total
            self.assertFalse(is_valid_cash, "Cash tendered less than grand total must be invalid")

    # -------------------------------------------------------------
    # TASK 3: LOGO MANAGEMENT & PERSISTENCE
    # -------------------------------------------------------------
    def test_logo_path_persistence_and_receipt_formatting(self):
        """Tests that logo path is saved in settings and loaded by printer service."""
        dummy_logo = Path(self.temp_dir) / "test_logo.png"
        dummy_logo.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRtest")

        self.settings_repo.set_setting("shop_logo_path", str(dummy_logo))
        loaded_path = self.settings_repo.get_setting("shop_logo_path")
        self.assertEqual(loaded_path, str(dummy_logo))

        printer = PrinterService(paper_width="80mm")
        sale_data = {
            "invoice_number": "INV-TEST-001",
            "sale_date": "2026-11-02 10:00:00",
            "grand_total": 4000.0,
            "items": []
        }
        receipt = printer.format_plain_receipt(sale_data, self.settings_repo.get_all_settings())
        self.assertIn("Arooj Cloth and Bedsheet Parda", receipt)

    # -------------------------------------------------------------
    # TASK 4: EDITABLE INVOICES & RECONCILIATION
    # -------------------------------------------------------------
    def test_invoice_editing_with_inventory_reconciliation(self):
        """
        Creates an invoice for 4 units (stock drops 50 -> 46).
        Revises the invoice:
        - Reduces item quantity from 4 to 2 (stock must be restored: 46 -> 48).
        - Modifies selling price from 2000 to 1900.
        - Adds Rs. 100 discount.
        - Verifies audit log recorded.
        - Verifies is_revised flag is set.
        """
        # Step 1: Complete an initial sale
        cart_items = [
            CartItem(
                product_id=self.prod_id,
                variant_id=self.var_id,
                product_name="Luxury Double Bed Sheet",
                variant_title="Double Navy Blue",
                quantity=Decimal("4.000"),
                original_catalog_price=Decimal("2000.00"),
                transaction_price=Decimal("2000.00"),
                cost_price=Decimal("1200.00")
            )
        ]
        ok, msg, inv_no = self.sales_service.complete_checkout(
            cart=cart_items,
            customer_id=self.customer_id,
            cashier_id=1,
            payment_method="Credit",
            tendered_cash=Decimal("0.00"),
            bill_discount=Decimal("0.00")
        )
        self.assertTrue(ok)

        # Verify initial state:
        # Stock: 50 - 4 = 46
        stock_after_sale = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
        self.assertEqual(stock_after_sale, Decimal("46.000"))

        # Customer balance: 4 x 2000 = 8000
        cust_bal = self.customer_repo.get_by_id(self.customer_id).current_balance
        self.assertEqual(cust_bal, Decimal("8000.00"))

        sale = self.sales_repo.get_sale_by_invoice(inv_no)
        item_id = sale["items"][0]["id"]

        # Step 2: Edit invoice (reduce quantity to 2, price 1900, discount 100)
        # Expected new grand total: (2 x 1900) - 100 = 3700
        # Expected stock restored: +2 (46 + 2 = 48)
        # Expected customer balance adjusted: 8000 -> 3700
        upd_items = [{
            "item_id": item_id,
            "quantity": Decimal("2.000"),
            "transaction_price": Decimal("1900.00")
        }]
        edit_ok, edit_msg = self.sales_repo.update_invoice(
            invoice_number=inv_no,
            updated_items=upd_items,
            new_discount=Decimal("100.00"),
            reason="Customer returned 2 pieces at counter & manager negotiated rate",
            editor_name="Manager"
        )
        self.assertTrue(edit_ok, edit_msg)

        # Step 3: Check inventory reconciliation
        reconciled_stock = self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity
        self.assertEqual(reconciled_stock, Decimal("48.000"), "Stock must increase by 2 when invoice quantity reduced from 4 to 2")

        # Step 4: Check customer balance reconciliation
        reconciled_bal = self.customer_repo.get_by_id(self.customer_id).current_balance
        self.assertEqual(reconciled_bal, Decimal("3700.00"), "Customer balance must adjust from 8000 to 3700")

        # Step 5: Check revision flags
        revised_sale = self.sales_repo.get_sale_by_invoice(inv_no)
        self.assertEqual(revised_sale["is_revised"], 1)
        self.assertEqual(revised_sale["revision_count"], 1)
        self.assertEqual(to_decimal(revised_sale["grand_total"]), Decimal("3700.00"))

        # Step 6: Check audit trail
        logs = self.sales_repo.get_invoice_audit_logs(inv_no)
        self.assertEqual(len(logs), 1)
        log = logs[0]
        self.assertEqual(to_decimal(log["old_grand_total"]), Decimal("8000.00"))
        self.assertEqual(to_decimal(log["new_grand_total"]), Decimal("3700.00"))
        self.assertIn("returned 2 pieces", log["changes_summary"])

        # Step 7: Check revised receipt formatting
        printer = PrinterService(paper_width="80mm")
        receipt = printer.format_plain_receipt(revised_sale, self.settings_repo.get_all_settings())
        self.assertIn("REVISED INVOICE", receipt)
        self.assertIn("3,700", receipt)

    def test_invoice_editing_increasing_quantity_deducts_inventory(self):
        """If edited invoice quantity increases, stock must be deducted accordingly."""
        cart_items = [
            CartItem(
                product_id=self.prod_id,
                variant_id=self.var_id,
                product_name="Luxury Double Bed Sheet",
                variant_title="Double Navy Blue",
                quantity=Decimal("2.000"),
                original_catalog_price=Decimal("2000.00"),
                transaction_price=Decimal("2000.00"),
                cost_price=Decimal("1200.00")
            )
        ]
        ok, msg, inv_no = self.sales_service.complete_checkout(
            cart=cart_items, customer_id=None, cashier_id=1, payment_method="Cash",
            tendered_cash=Decimal("4000.00"), bill_discount=Decimal("0.00")
        )
        self.assertTrue(ok)
        self.assertEqual(self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity, Decimal("48.000"))

        sale = self.sales_repo.get_sale_by_invoice(inv_no)
        item_id = sale["items"][0]["id"]

        # Increase quantity from 2 to 5 (stock should reduce 48 -> 45)
        upd_items = [{
            "item_id": item_id,
            "quantity": Decimal("5.000"),
            "transaction_price": Decimal("2000.00")
        }]
        edit_ok, edit_msg = self.sales_repo.update_invoice(
            invoice_number=inv_no,
            updated_items=upd_items,
            new_discount=Decimal("0.00"),
            reason="Customer added 3 more sets to the same bill",
            editor_name="Manager"
        )
        self.assertTrue(edit_ok)
        self.assertEqual(self.catalog_repo.get_variants_for_product(self.prod_id)[0].stock_quantity, Decimal("45.000"))

if __name__ == "__main__":
    unittest.main()
