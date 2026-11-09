"""
Tests for Arooj POS v2 Features and Architecture Mandates
Covers:
1. Local Database Isolation (%LOCALAPPDATA%/AroojPOS_v2/arooj_pos_v2.db)
2. Screen Constructor Signature Safety
3. Gaz to Meter and Meter to Gaz conversions (0.9144 factor)
4. Pakistani WhatsApp Phone Formatting
5. Cart Item Price Overrides & 15% Discount Manager PIN Gate
6. Dual Receipt Formatting (80mm vs 58mm)
7. Dark and Light Theme QSS stylesheets
"""

import unittest
import os
import inspect
from decimal import Decimal
from pathlib import Path

from app.config import (
    get_db_path, get_app_data_dir, gaz_to_meters, meters_to_gaz,
    format_pakistani_whatsapp_number, to_decimal, to_qty_decimal
)
from app.ui.supplier_screen import SupplierScreen
from app.ui.expense_screen import ExpenseScreen
from app.ui.customer_management import CustomerManagementScreen, CustomerScreen
from app.ui.inventory_screen import InventoryScreen
from app.ui.theme_manager import get_theme_qss, LIGHT_THEME_QSS, DARK_THEME_QSS
from app.services.printer_service import PrinterService
from app.models.entities import CartItem, Product, ProductVariant, User
from app.services.sales_service import SalesService
from app.repositories.sales_repository import SalesRepository
from app.repositories.user_repository import UserRepository
from app.repositories.settings_repository import SettingsRepository


class TestV2Features(unittest.TestCase):
    def test_database_isolation_path(self):
        """Mandate 1: Database path must use AroojPOS_v2 and arooj_pos_v2.db."""
        # Unset custom override if present to test standard path
        old_env = os.environ.pop("AROOJ_POS_DB_PATH", None)
        try:
            app_dir = get_app_data_dir()
            db_path = get_db_path()
            self.assertIn("AroojPOS_v2", str(app_dir))
            self.assertEqual(db_path.name, "arooj_pos_v2.db")
            self.assertEqual(db_path.parent, app_dir)
        finally:
            if old_env is not None:
                os.environ["AROOJ_POS_DB_PATH"] = old_env

    def test_fabric_unit_conversions(self):
        """Mandate E: 1 Gaz = 0.9144 Meters and fractional precision."""
        # 1 Gaz = 0.9144 Meters
        m = gaz_to_meters(Decimal("1.0"))
        self.assertEqual(m, Decimal("0.914"))

        # 100 Gaz = 91.44 Meters
        m100 = gaz_to_meters(Decimal("100.0"))
        self.assertEqual(m100, Decimal("91.440"))

        # Meter to Gaz inverse
        g = meters_to_gaz(Decimal("0.9144"))
        self.assertAlmostEqual(float(g), 1.0, places=2)

        # Fractional fabric length
        frac_gaz = Decimal("120.5")
        frac_m = gaz_to_meters(frac_gaz)
        self.assertEqual(frac_m, Decimal("110.185"))

    def test_whatsapp_phone_formatting(self):
        """Verifies normalization of Pakistani phone numbers for WhatsApp click-to-chat links."""
        # Standard local cell: 03001234567 -> 923001234567
        self.assertEqual(format_pakistani_whatsapp_number("03001234567"), "923001234567")
        self.assertEqual(format_pakistani_whatsapp_number("0300-1234567"), "923001234567")
        self.assertEqual(format_pakistani_whatsapp_number("+92 300 1234567"), "923001234567")
        self.assertEqual(format_pakistani_whatsapp_number("0321 9876543"), "923219876543")

    def test_constructor_signature_safety(self):
        """
        Mandate 2: Ensure screen constructors accept the exact arguments passed by MainWindow:
        - SupplierScreen(supplier_repo, catalog_repo=None, parent=None)
        - ExpenseScreen(expense_repo, parent=None)
        - CustomerScreen(customer_repo, parent=None)
        - InventoryScreen(inventory_repo, catalog_repo=None, parent=None)
        """
        # SupplierScreen
        supp_sig = inspect.signature(SupplierScreen.__init__)
        params = list(supp_sig.parameters.keys())
        self.assertEqual(params[0], "self")
        self.assertEqual(params[1], "supplier_repo")
        self.assertIn("catalog_repo", params)

        # ExpenseScreen
        exp_sig = inspect.signature(ExpenseScreen.__init__)
        params = list(exp_sig.parameters.keys())
        self.assertEqual(params[0], "self")
        self.assertEqual(params[1], "expense_repo")

        # CustomerScreen & CustomerManagementScreen
        cust_sig = inspect.signature(CustomerScreen.__init__)
        params = list(cust_sig.parameters.keys())
        self.assertEqual(params[0], "self")
        self.assertEqual(params[1], "customer_repo")

        # InventoryScreen
        inv_sig = inspect.signature(InventoryScreen.__init__)
        params = list(inv_sig.parameters.keys())
        self.assertEqual(params[0], "self")
        self.assertEqual(params[1], "inventory_repo")
        self.assertIn("catalog_repo", params)

    def test_theme_stylesheets(self):
        """Feature A: Verifies Dark Mode (#1e1e1e) and Light Mode (#f8f9fa) stylesheets."""
        dark_qss = get_theme_qss("dark")
        light_qss = get_theme_qss("light")

        self.assertIn("#1e1e1e", dark_qss)
        self.assertIn("#0d9488", dark_qss)
        self.assertIn("#f8f9fa", light_qss)
        self.assertIn("#059669", light_qss)

    def test_dual_receipt_formatting(self):
        """Feature B: Verifies both 80mm (48 cols) and 58mm (32 cols) receipt layouts."""
        printer_80 = PrinterService(paper_width="80mm")
        printer_58 = PrinterService(paper_width="58mm")

        self.assertEqual(printer_80.cols, 48)
        self.assertEqual(printer_58.cols, 32)

        sample_sale = {
            "invoice_number": "INV-2026-9999",
            "sale_date": "2026-10-30 14:30:00",
            "cashier_name": "Senior Cashier",
            "customer_name": "Haji Muhammad",
            "customer_phone": "03001234567",
            "items": [
                {
                    "product_name": "Luxury Velvet Bedsheet",
                    "size": "King",
                    "color": "Maroon",
                    "unit_name": "Set",
                    "quantity": 1.0,
                    "unit_price": 4500.0,
                    "transaction_price": 4500.0,
                    "line_total": 4500.0
                }
            ],
            "subtotal": 4500.0,
            "discount_amount": 0.0,
            "tax_amount": 0.0,
            "grand_total": 4500.0,
            "paid_amount": 5000.0,
            "change_amount": 500.0,
            "payments": [{"payment_method": "Cash", "amount": 5000.0, "change_returned": 500.0}]
        }
        settings = {
            "shop_name": "Arooj Cloth and Bedsheet Parda",
            "shop_name_urdu": "عروج کلوتھ اینڈ بیڈ شیٹ پردہ",
            "shop_address": "Main Bazar, Pakistan",
            "shop_phone": "0300-1234567"
        }

        rec_80 = printer_80.format_plain_receipt(sample_sale, settings)
        rec_58 = printer_58.format_plain_receipt(sample_sale, settings)

        self.assertIn("Arooj Cloth and Bedsheet Parda", rec_80)
        self.assertIn("INV-2026-9999", rec_80)
        self.assertIn("Rs. 4,500.00", rec_80)
        self.assertIn("03001234567", rec_80)

        self.assertIn("Arooj Cloth and Bedsheet Parda", rec_58)
        self.assertIn("INV-2026-9999", rec_58)
        self.assertIn("Rs. 4,500.00", rec_58)

        # Check line widths
        for line in rec_80.splitlines():
            # Multibyte urdu or standard line length checks
            if not any(ord(char) > 127 for char in line):
                self.assertLessEqual(len(line), 48)

    def test_cart_item_bargain_price_and_pin_gate(self):
        """Feature B: Verifies spot bargain price override and 15% discount limit Manager PIN gate."""
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        from app.migrations import apply_migrations
        apply_migrations(conn)

        user_repo = UserRepository(conn)
        settings_repo = SettingsRepository(conn)
        sales_repo = SalesRepository(conn)
        sales_service = SalesService(sales_repo, user_repo, settings_repo)

        # Ensure manager PIN is 1234
        settings_repo.set_setting("manager_pin", "1234")
        settings_repo.set_setting("max_cashier_discount_percent", "15.0")

        # Cashier user
        cashier = User(id=2, username="cashier1", full_name="Cashier One", role="cashier", password_hash="dummy_hash", salt="dummy_salt", is_active=True)

        item = CartItem(
            product_id=1,
            product_name="Winter Double Razai",
            sku="RZ-001",
            unit_name="Pcs",
            quantity=Decimal("1.000"),
            original_catalog_price=Decimal("4000.00"),
            transaction_price=Decimal("4000.00"),
            cost_price=Decimal("2500.00")
        )

        # 1. 10% discount: Rs. 3600 (within 15% limit) -> Should succeed without Manager PIN
        ok, msg = sales_service.update_cart_item_price(item, Decimal("3600.00"), current_user=cashier)
        self.assertTrue(ok)
        self.assertEqual(item.transaction_price, Decimal("3600.00"))
        self.assertTrue(item.is_price_overridden)
        self.assertEqual(item.original_catalog_price, Decimal("4000.00"))  # Master catalog price unmodified

        # 2. 25% discount: Rs. 3000 (exceeds 15% limit) without PIN -> Should fail
        ok, msg = sales_service.update_cart_item_price(item, Decimal("3000.00"), current_user=cashier)
        self.assertFalse(ok)
        self.assertIn("Manager PIN", msg)

        # 3. 25% discount with wrong PIN -> Should fail
        ok, msg = sales_service.update_cart_item_price(item, Decimal("3000.00"), current_user=cashier, manager_pin="9999")
        self.assertFalse(ok)

        # 4. 25% discount with correct Manager PIN "1234" -> Should succeed
        ok, msg = sales_service.update_cart_item_price(item, Decimal("3000.00"), current_user=cashier, manager_pin="1234")
        self.assertTrue(ok)
        self.assertEqual(item.transaction_price, Decimal("3000.00"))
        self.assertEqual(item.override_approved_by, "Manager Authorized")


if __name__ == "__main__":
    unittest.main()
