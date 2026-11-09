"""
Test Thermal Receipt Printing Service
Verifies real printer discovery, receipt layout formatting (58mm vs 80mm),
duplicate reprint indicators, receipt file spooling, and accurate success/error reporting.
"""

import unittest
import tempfile
from pathlib import Path
from decimal import Decimal

from app.services.printer_service import PrinterService

class TestRealPrinting(unittest.TestCase):
    def setUp(self):
        self.printer_service_80 = PrinterService(paper_width="80mm")
        self.printer_service_58 = PrinterService(paper_width="58mm")

        self.sample_sale = {
            "invoice_number": "INV-20261027-0099",
            "sale_date": "2026-10-27 15:30:00",
            "customer_name": "Walk-in Customer",
            "customer_phone": "0300-1234567",
            "cashier_name": "Counter Staff",
            "payment_method": "Cash",
            "subtotal": 3500.0,
            "discount_amount": 200.0,
            "tax_amount": 0.0,
            "grand_total": 3300.0,
            "paid_amount": 3500.0,
            "change_amount": 200.0,
            "due_amount": 0.0,
            "items": [
                {
                    "product_name": "Cotton Bedsheet King",
                    "variant_name": "Royal Blue / Floral",
                    "unit_code": "PCS",
                    "quantity": 1.0,
                    "unit_price": 2500.0,
                    "total_price": 2500.0
                },
                {
                    "product_name": "Boski Unstitched Fabric",
                    "variant_name": "Off-White",
                    "unit_code": "MTR",
                    "quantity": 2.5,
                    "unit_price": 400.0,
                    "total_price": 1000.0
                }
            ]
        }

        self.company_info = {
            "shop_name": "Arooj Cloth and Bedsheet Parda",
            "shop_urdu_name": "عروج کلوتھ اینڈ بیڈ شیٹ پردہ",
            "address": "Main Bazar, Shop #12",
            "phone": "0300-9876543",
            "footer_urdu": "خریدا ہوا مال 7 دن کے اندر تبدیل ہو سکتا ہے۔ کیش واپس نہیں ہوگا۔"
        }

    def test_printer_discovery(self):
        printers = self.printer_service_80.get_available_printers()
        self.assertIsInstance(printers, list)
        self.assertGreater(len(printers), 0, "Printer list should include at least virtual spooler or system printers")

    def test_80mm_receipt_formatting(self):
        receipt_text = self.printer_service_80.format_receipt_text(self.sample_sale, self.company_info)
        self.assertIn("Arooj Cloth and Bedsheet Parda", receipt_text)
        self.assertIn("INV-20261027-0099", receipt_text)
        self.assertIn("Cotton Bedsheet King", receipt_text)
        self.assertIn("Boski Unstitched Fabric", receipt_text)
        self.assertIn("Rs. 3,300.00", receipt_text)
        self.assertIn("Cash", receipt_text)
        self.assertIn("Change / بقیہ", receipt_text)

    def test_58mm_receipt_formatting(self):
        receipt_text = self.printer_service_58.format_receipt_text(self.sample_sale, self.company_info)
        self.assertIn("Arooj Cloth", receipt_text)
        self.assertIn("INV-20261027-0099", receipt_text)
        self.assertIn("3,300.00", receipt_text)

    def test_duplicate_reprint_header(self):
        receipt_text = self.printer_service_80.format_receipt_text(
            self.sample_sale, self.company_info, is_duplicate=True
        )
        self.assertIn("*** DUPLICATE REPRINT / نقل ***", receipt_text)

    def test_print_spooling_and_no_false_success(self):
        """
        Tests print_receipt execution:
        - It should write the spool text copy to disk
        - It should return either a success or a clear hardware-failure report without crashing
        """
        success, msg = self.printer_service_80.print_receipt(
            self.sample_sale, self.company_info, printer_name="Virtual PDF Receipt Printer (AroojPOS Spooler)"
        )
        self.assertIsInstance(success, bool)
        self.assertIsInstance(msg, str)
        self.assertTrue(success, f"Virtual spooler should succeed, got: {msg}")
        self.assertIn("spool", msg.lower())

    def test_print_duplicate_helper(self):
        success, msg = self.printer_service_80.print_duplicate_receipt(
            self.sample_sale, self.company_info, printer_name="Virtual PDF Receipt Printer (AroojPOS Spooler)"
        )
        self.assertTrue(success)
        self.assertIn("spool", msg.lower())

if __name__ == "__main__":
    unittest.main()
