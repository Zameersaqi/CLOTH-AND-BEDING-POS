"""
Test End-of-Day Cash Register Closing, Expense Tracking, and Supplier Purchases
"""

import unittest
import tempfile
from pathlib import Path
from decimal import Decimal

from app.database import DatabaseManager
from app.migrations import apply_migrations
from app.seed import seed_database
from app.repositories import ExpenseRepository, SupplierRepository, SalesRepository
from app.models.entities import Expense

class TestCashRegisterAndOperations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_ops.db"
        self.db_mgr = DatabaseManager(self.db_path)
        self.conn = self.db_mgr.get_connection()
        apply_migrations(self.conn)
        seed_database(self.conn)

        self.expense_repo = ExpenseRepository(self.conn)
        self.supplier_repo = SupplierRepository(self.conn)
        self.sales_repo = SalesRepository(self.conn)

    def tearDown(self):
        self.db_mgr.close()
        self.temp_dir.cleanup()

    def test_record_expenses(self):
        exp1 = Expense(
            id=None,
            category="Tea & Refreshment",
            amount=Decimal("250.00"),
            payment_method="Cash",
            description="Guest tea and water",
            recorded_by=1
        )
        exp_id = self.expense_repo.add_expense(exp1)
        self.assertIsNotNone(exp_id)

        exp2 = Expense(
            id=None,
            category="Shop Rent",
            amount=Decimal("15000.00"),
            payment_method="Bank Transfer",
            description="Monthly advance",
            recorded_by=1
        )
        self.expense_repo.add_expense(exp2)

        expenses = self.expense_repo.get_expenses()
        self.assertEqual(len(expenses), 2)

    def test_cash_shift_reconciliation(self):
        # 1. Opening cash float
        opening_float = Decimal("5000.00")

        # 2. Add an expense paid from till cash
        exp = Expense(
            id=None,
            category="Packaging & Shopping Bags",
            amount=Decimal("600.00"),
            payment_method="Cash",
            description="5kg plastic carrier bags",
            recorded_by=1
        )
        self.expense_repo.add_expense(exp)

        # 3. Simulate a cash sale
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sales (
                invoice_number, customer_id, cashier_id, subtotal, discount_amount,
                tax_amount, grand_total, paid_amount, balance_amount, payment_method,
                payment_status, is_returned
            ) VALUES (
                'INV-TEST-CASH', 1, 1, 4000.00, 0.00,
                0.00, 4000.00, 4000.00, 0.00, 'Cash',
                'Paid', 0
            );
        """)
        self.conn.commit()

        # 4. Calculate expected cash
        # Expected = Opening (5000) + Cash Sales (4000) - Cash Expenses (600) = 8400.00
        cursor.execute("""
            SELECT COALESCE(SUM(paid_amount), 0)
            FROM sales
            WHERE payment_method = 'Cash' AND DATE(sale_date) = DATE('now', 'localtime') AND is_returned = 0;
        """)
        cash_sales = Decimal(str(cursor.fetchone()[0]))
        self.assertEqual(cash_sales, Decimal("4000.00"))

        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE payment_method LIKE '%Cash%' AND DATE(expense_date) = DATE('now', 'localtime');
        """)
        cash_expenses = Decimal(str(cursor.fetchone()[0]))
        self.assertEqual(cash_expenses, Decimal("600.00"))

        expected_cash = opening_float + cash_sales - cash_expenses
        self.assertEqual(expected_cash, Decimal("8400.00"))

        # 5. Record shift closing with actual cash count
        actual_cash = Decimal("8400.00")
        diff = actual_cash - expected_cash

        cursor.execute("""
            INSERT INTO cash_registers (
                cashier_id, opening_cash, total_cash_sales, total_expenses,
                expected_cash, actual_cash, discrepancy, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Shift closed', 'closed');
        """, (
            1, float(opening_float), float(cash_sales), float(cash_expenses),
            float(expected_cash), float(actual_cash), float(diff)
        ))
        self.conn.commit()

        cursor.execute("SELECT expected_cash, actual_cash, discrepancy FROM cash_registers WHERE cashier_id = 1;")
        row = cursor.fetchone()
        self.assertEqual(Decimal(str(row[0])), Decimal("8400.00"))
        self.assertEqual(Decimal(str(row[1])), Decimal("8400.00"))
        self.assertEqual(Decimal(str(row[2])), Decimal("0.00"))

    def test_supplier_purchase_and_balance_update(self):
        # 1. Create a supplier
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO suppliers (code, company_name, contact_person, phone, opening_balance, current_balance)
            VALUES ('SUP-GUL', 'Gul Ahmed Textile Mills', 'Haji Irfan', '0300-1112233', 0.00, 0.00);
        """)
        supp_id = cursor.lastrowid
        self.conn.commit()

        # 2. Record purchase bill of Rs. 50,000 with partial cash paid of Rs. 20,000
        pur_id = self.supplier_repo.record_purchase(
            purchase_invoice_no="PUR-2026-001",
            supplier_id=supp_id,
            subtotal=Decimal("50000.00"),
            tax_amount=Decimal("0.00"),
            grand_total=Decimal("50000.00"),
            paid_amount=Decimal("20000.00"),
            items=[]
        )
        self.assertIsNotNone(pur_id)

        # 3. Verify supplier payable balance increased by remaining Rs. 30,000
        supp = self.supplier_repo.get_by_id(supp_id)
        self.assertEqual(supp.current_balance, Decimal("30000.00"))

if __name__ == "__main__":
    unittest.main()
