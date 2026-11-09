"""
Expense Repository for Shop Daily Expenses and Cash Management
"""

import sqlite3
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal
from app.models.entities import Expense
from app.config import to_decimal

class ExpenseRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add_expense(self, expense: Union[Expense, dict]) -> int:
        if isinstance(expense, dict):
            expense = Expense(
                id=expense.get("id"),
                category=expense.get("category", ""),
                amount=to_decimal(expense.get("amount", 0)),
                payment_method=expense.get("payment_method", "cash"),
                description=expense.get("description"),
                receipt_ref=expense.get("receipt_ref") or expense.get("reference_number"),
                recorded_by=expense.get("recorded_by") or expense.get("user_id", 1),
                expense_date=expense.get("expense_date")
            )

        cursor = self.conn.cursor()
        if expense.expense_date:
            dt_str = expense.expense_date
            if " " not in dt_str:
                dt_str = f"{dt_str} 12:00:00"
            cursor.execute("""
                INSERT INTO expenses (category, amount, payment_method, description, receipt_ref, recorded_by, expense_date)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                expense.category, float(expense.amount), expense.payment_method,
                expense.description, expense.receipt_ref, expense.recorded_by, dt_str
            ))
        else:
            cursor.execute("""
                INSERT INTO expenses (category, amount, payment_method, description, receipt_ref, recorded_by, expense_date)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP);
            """, (
                expense.category, float(expense.amount), expense.payment_method,
                expense.description, expense.receipt_ref, expense.recorded_by
            ))
        expense_id = cursor.lastrowid
        self.conn.commit()
        return expense_id

    create_expense = add_expense

    def get_expenses(self, start_date: Optional[str] = None, end_date: Optional[str] = None, category: Optional[str] = None) -> List[dict]:
        cursor = self.conn.cursor()
        query = "SELECT e.*, u.full_name as user_name FROM expenses e LEFT JOIN users u ON e.recorded_by = u.id WHERE 1=1"
        params = []
        if start_date:
            query += " AND DATE(e.expense_date) >= DATE(?)"
            params.append(start_date)
        if end_date:
            query += " AND DATE(e.expense_date) <= DATE(?)"
            params.append(end_date)
        if category and category != "All":
            term = f"%{category.strip()}%"
            query += " AND e.category LIKE ?"
            params.append(term)
        query += " ORDER BY e.id DESC;"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

    def update_expense(
        self,
        expense_id: int,
        category: Union[str, dict] = "",
        amount: Decimal = Decimal("0.00"),
        payment_method: str = "Cash",
        description: Optional[str] = None,
        receipt_ref: Optional[str] = None,
        **kwargs
    ) -> bool:
        if isinstance(category, dict):
            d = category
            amount = to_decimal(d.get("amount", 0))
            payment_method = d.get("payment_method", "Cash")
            description = d.get("description")
            receipt_ref = d.get("receipt_ref") or d.get("reference_number")
            category = d.get("category", "")

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE expenses
            SET category = ?, amount = ?, payment_method = ?, description = ?, receipt_ref = ?
            WHERE id = ?;
        """, (category, float(amount), payment_method, description, receipt_ref, expense_id))
        self.conn.commit()
        return True

    def delete_expense(self, expense_id: int) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?;", (expense_id,))
        self.conn.commit()
        return True

    def get_summary(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        base_filter = " WHERE 1=1"
        params = []
        if start_date:
            base_filter += " AND DATE(expense_date) >= DATE(?)"
            params.append(start_date)
        if end_date:
            base_filter += " AND DATE(expense_date) <= DATE(?)"
            params.append(end_date)

        cursor.execute("SELECT SUM(amount) FROM expenses" + base_filter, params)
        val = cursor.fetchone()[0] or 0.0

        # Group by category
        cursor.execute("SELECT category, SUM(amount) FROM expenses" + base_filter + " GROUP BY category;", params)
        categories = {r[0]: to_decimal(r[1]) for r in cursor.fetchall()}

        # Group by payment method
        cursor.execute("SELECT payment_method, SUM(amount) FROM expenses" + base_filter + " GROUP BY payment_method;", params)
        by_method = {r[0]: to_decimal(r[1]) for r in cursor.fetchall()}

        return {
            "total_expenses": to_decimal(val),
            "total_amount": to_decimal(val),
            "categories": categories,
            "by_method": by_method
        }

