"""
Tests for Phase 6 Dedicated Daily Shop Expenses Screen & Reporting.
"""

import unittest
from decimal import Decimal
from datetime import date, timedelta
from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories.expense_repository import ExpenseRepository
from app.models.entities import Expense


class TestExpenses(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(":memory:")
        self.conn = self.db.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)
        self.repo = ExpenseRepository(self.conn)

    def tearDown(self):
        self.db.close()

    def test_record_expense_with_all_fields(self):
        exp = Expense(
            category="Shop Rent (دکان کرایہ)",
            amount=Decimal("35000.00"),
            payment_method="bank",
            description="Monthly shop rent for ground floor",
            reference_number="RENT-OCT-2026",
            user_id=1
        )
        exp_id = self.repo.create_expense(exp)
        self.assertIsNotNone(exp_id)

        all_exp = self.repo.get_expenses()
        matching = [e for e in all_exp if e["id"] == exp_id]
        self.assertEqual(len(matching), 1)
        saved = matching[0]
        self.assertEqual(Decimal(str(saved["amount"])), Decimal("35000.00"))
        self.assertEqual(saved["payment_method"], "bank")
        self.assertEqual(saved["receipt_ref"], "RENT-OCT-2026")

    def test_filter_expenses_by_category_and_date(self):
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        # Add tea expense
        self.repo.create_expense(Expense(
            category="Tea & Refreshment (چائے / پانی)",
            amount=Decimal("150.00"),
            payment_method="cash",
            description="Evening guest tea",
            user_id=1,
            expense_date=today
        ))

        # Add electricity bill
        self.repo.create_expense(Expense(
            category="Electricity & Utilities (بجلی / بل)",
            amount=Decimal("4200.00"),
            payment_method="bank",
            description="LESCO shop electricity bill",
            user_id=1,
            expense_date=today
        ))

        # Filter by category
        tea_expenses = self.repo.get_expenses(category="Tea")
        self.assertGreaterEqual(len(tea_expenses), 1)
        self.assertTrue(all("Tea" in e["category"] for e in tea_expenses))

        # Filter by date range
        today_expenses = self.repo.get_expenses(start_date=today, end_date=today)
        self.assertGreaterEqual(len(today_expenses), 2)

    def test_expense_summary_calculation(self):
        self.repo.create_expense(Expense(
            category="Freight & Transport (کرایہ مال / اڈہ)",
            amount=Decimal("800.00"),
            payment_method="cash",
            user_id=1
        ))
        self.repo.create_expense(Expense(
            category="Packaging & Shopping Bags (شاپنگ بیگز)",
            amount=Decimal("1200.00"),
            payment_method="cash",
            user_id=1
        ))

        summary = self.repo.get_summary()
        self.assertGreaterEqual(summary["total_amount"], Decimal("2000.00"))
        self.assertIn("categories", summary)
        self.assertIn("by_method", summary)

    def test_update_and_delete_expense(self):
        exp_id = self.repo.create_expense(Expense(
            category="Other Expense (متفرق خرچہ)",
            amount=Decimal("500.00"),
            payment_method="cash",
            description="Initial note",
            user_id=1
        ))

        # Update
        update_data = {
            "category": "Shop Maintenance & Repairs (مرمت / خرچہ)",
            "amount": Decimal("650.00"),
            "payment_method": "cash",
            "description": "Counter light bulb and tube repair",
            "reference_number": "REP-01"
        }
        success = self.repo.update_expense(exp_id, update_data)
        self.assertTrue(success)

        cur = self.conn.cursor()
        cur.execute("SELECT amount, category, description FROM expenses WHERE id = ?", (exp_id,))
        row = cur.fetchone()
        self.assertEqual(Decimal(str(row["amount"])), Decimal("650.00"))
        self.assertEqual(row["description"], "Counter light bulb and tube repair")

        # Delete / Void
        del_success = self.repo.delete_expense(exp_id)
        self.assertTrue(del_success)

        cur.execute("SELECT id FROM expenses WHERE id = ?", (exp_id,))
        self.assertIsNone(cur.fetchone())


if __name__ == "__main__":
    unittest.main()
