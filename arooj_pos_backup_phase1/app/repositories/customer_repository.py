"""
Customer Repository for Customer Management, Credit Sales, and Ledger Tracking
"""

import sqlite3
from typing import List, Optional
from decimal import Decimal
from app.models.entities import Customer
from app.config import to_decimal

class CustomerRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_all(self, search: Optional[str] = None) -> List[Customer]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM customers WHERE is_active = 1"
        params = []
        if search:
            query += " AND (name LIKE ? OR phone LIKE ? OR code LIKE ?)"
            s = f"%{search.strip()}%"
            params.extend([s, s, s])
        query += " ORDER BY name ASC;"
        cursor.execute(query, params)
        return [
            Customer(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                phone=r["phone"],
                address=r["address"],
                city=r["city"],
                credit_limit=to_decimal(r["credit_limit"]),
                opening_balance=to_decimal(r["opening_balance"]),
                current_balance=to_decimal(r["current_balance"]),
                discount_percent=to_decimal(r["discount_percent"]),
                notes=r["notes"],
                is_active=bool(r["is_active"])
            ) for r in cursor.fetchall()
        ]

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE id = ?;", (customer_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return Customer(
            id=r["id"],
            code=r["code"],
            name=r["name"],
            phone=r["phone"],
            address=r["address"],
            city=r["city"],
            credit_limit=to_decimal(r["credit_limit"]),
            opening_balance=to_decimal(r["opening_balance"]),
            current_balance=to_decimal(r["current_balance"]),
            discount_percent=to_decimal(r["discount_percent"]),
            notes=r["notes"],
            is_active=bool(r["is_active"])
        )

    def create(self, cust: Customer) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO customers (code, name, phone, address, city, credit_limit, opening_balance, current_balance, discount_percent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            cust.code, cust.name, cust.phone, cust.address, cust.city,
            float(cust.credit_limit), float(cust.opening_balance), float(cust.opening_balance),
            float(cust.discount_percent), cust.notes
        ))
        cust_id = cursor.lastrowid
        if cust.opening_balance > Decimal("0.00"):
            cursor.execute("""
                INSERT INTO customer_ledger (customer_id, transaction_type, debit, credit, running_balance, description)
                VALUES (?, 'opening_balance', ?, 0.0, ?, 'Opening Balance');
            """, (cust_id, float(cust.opening_balance), float(cust.opening_balance)))
        self.conn.commit()
        return cust_id

    def receive_payment(self, customer_id: int, payment_amount: Decimal, payment_method: str, notes: str) -> Decimal:
        """Records a customer paying towards their outstanding ledger without creating a fake sale."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT current_balance FROM customers WHERE id = ?;", (customer_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Customer {customer_id} not found")

        old_bal = to_decimal(row[0])
        new_bal = old_bal - payment_amount

        cursor.execute("UPDATE customers SET current_balance = ? WHERE id = ?;", (float(new_bal), customer_id))
        cursor.execute("""
            INSERT INTO customer_ledger (customer_id, transaction_type, debit, credit, running_balance, description)
            VALUES (?, 'payment_received', 0.0, ?, ?, ?);
        """, (customer_id, float(payment_amount), float(new_bal), f"Received payment via {payment_method}: {notes}"))
        self.conn.commit()
        return new_bal

    def get_customer_statement(self, customer_id: int) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT cl.*, s.invoice_number
            FROM customer_ledger cl
            LEFT JOIN sales s ON cl.sale_id = s.id
            WHERE cl.customer_id = ?
            ORDER BY cl.created_at ASC, cl.id ASC;
        """, (customer_id,))
        return [dict(r) for r in cursor.fetchall()]
