"""
Test Reports, Cost of Goods Sold (COGS), Gross Profit, Expenses, and Net Profit
"""

import unittest
import tempfile
from decimal import Decimal
from pathlib import Path
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories import CatalogRepository, SalesRepository, ExpenseRepository, UserRepository, SettingsRepository
from app.services.sales_service import SalesService
from app.services.report_service import ReportService
from app.models.entities import Expense

class TestReportsProfit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_reports.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)

        self.cat_repo = CatalogRepository(self.conn)
        self.sales_repo = SalesRepository(self.conn)
        self.exp_repo = ExpenseRepository(self.conn)
        self.user_repo = UserRepository(self.conn)
        self.settings_repo = SettingsRepository(self.conn)
        self.sales_service = SalesService(self.sales_repo, self.user_repo, self.settings_repo)
        self.report_service = ReportService(self.conn)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_profit_and_cogs_calculation(self):
        # 1. Product with Cost = 1200, Selling Price = 2000
        prods = self.cat_repo.get_products()
        p = prods[0]
        v = p.variants[0]
        self.cat_repo.update_variant_pricing_stock(v.id, Decimal("1200.00"), Decimal("2000.00"), Decimal("10.000"))
        p = self.cat_repo.get_product_by_id(p.id)
        v = p.variants[0]

        # 2. Sell 2 units = Revenue 4000, COGS = 2400, Gross Profit = 1600
        cart = []
        self.sales_service.add_to_cart(cart, p, v, Decimal("2.000"))
        ok, msg, inv_no = self.sales_service.complete_checkout(cart, None, 1, "Cash", Decimal("4000.00"))
        self.assertTrue(ok)

        # 3. Record an operational expense of Rs. 400 (e.g. shop tea & electricity)
        exp = Expense(
            id=None,
            category="Shop Utilities",
            amount=Decimal("400.00"),
            payment_method="Cash",
            description="Tea and utility bills",
            recorded_by=1
        )
        self.exp_repo.add_expense(exp)

        # 4. Check Dashboard Financial Metrics
        summary = self.report_service.get_dashboard_summary()
        self.assertEqual(summary["total_revenue"], Decimal("4000.00"))
        self.assertEqual(summary["cogs"], Decimal("2400.00"))
        self.assertEqual(summary["gross_profit"], Decimal("1600.00"))  # 4000 - 2400
        self.assertEqual(summary["expenses"], Decimal("400.00"))
        self.assertEqual(summary["net_profit"], Decimal("1200.00"))   # 1600 - 400

if __name__ == "__main__":
    unittest.main()
