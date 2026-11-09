"""
Tests for Phase 2 & Phase 3 Thermal Barcode Label Generation, Receipt Logo Embedding, and Printer Service.
"""

import unittest
from pathlib import Path
from decimal import Decimal
from app.services.printer_service import PrinterService
from app.config import get_app_data_dir


class TestLabelAndPrinter(unittest.TestCase):
    def setUp(self):
        self.printer_service = PrinterService(paper_width="80mm")

    def test_printer_discovery_returns_list(self):
        printers = self.printer_service.get_available_printers()
        self.assertIsInstance(printers, list)
        self.assertGreater(len(printers), 0)

    def test_thermal_receipt_includes_logo_html_when_path_set(self):
        # Create a temporary logo file
        logo_dir = get_app_data_dir() / "logos"
        logo_dir.mkdir(parents=True, exist_ok=True)
        test_logo = logo_dir / "test_logo.png"
        test_logo.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

        settings = {
            "shop_name": "Arooj Cloth and Bedsheet Parda",
            "shop_name_urdu": "عروج کلوتھ اینڈ بیڈ شیٹ پردہ",
            "shop_phone": "0300-1234567",
            "shop_address": "Main Commercial Market",
            "receipt_paper_width": "80mm",
            "shop_logo_path": str(test_logo)
        }
        sale_data = {
            "invoice_number": "INV-20261028-0001",
            "sale_date": "2026-10-28 14:30:00",
            "subtotal": 1000.0,
            "grand_total": 1000.0,
            "paid_amount": 1000.0,
            "items": []
        }

        html = self.printer_service.generate_html_receipt(sale_data, settings)
        self.assertIn("<img src=\"file:///", html)
        self.assertIn("test_logo.png", html)

    def test_test_receipt_printing(self):
        settings = {
            "shop_name": "Arooj Cloth and Bedsheet Parda",
            "receipt_paper_width": "80mm"
        }
        # In headless environment, Virtual spooler printer succeeds
        success, msg = self.printer_service.print_test_receipt(settings, printer_name="Default Thermal Printer (Virtual / Spooler)")
        self.assertTrue(success)
        self.assertIn("spooled successfully", msg)


if __name__ == "__main__":
    unittest.main()
