"""
Expense Repository for Shop Daily Expenses and Cash Management
"""

import sqlite3
from typing import List, Optional
from decimal import Decimal
from app.models.entities import Expense
from app.config import to_decimal

class ExpenseRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add_expense(self, expense: Expense) -> int:
        cursor = self.conn.cursor()
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

    def get_expenses(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[dict]:
        cursor = self.conn.cursor()
        query = "SELECT e.*, u.full_name as user_name FROM expenses e LEFT JOIN users u ON e.recorded_by = u.id WHERE 1=1"
        params = []
        if start_date:
            query += " AND DATE(e.expense_date) >= DATE(?)"
            params.append(start_date)
        if end_date:
            query += " AND DATE(e.expense_date) <= DATE(?)"
            params.append(end_date)
        query += " ORDER BY e.id DESC;"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
