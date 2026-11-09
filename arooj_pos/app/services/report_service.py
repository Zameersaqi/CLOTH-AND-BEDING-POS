"""
Report Service: Business Intelligence, Financial Auditing, Profit Calculation, and Sales Summaries
"""

import sqlite3
from typing import Dict, Any, List, Optional
from decimal import Decimal
from app.config import to_decimal, to_qty_decimal

class ReportService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_dashboard_summary(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculates today's real-time financial stats:
        - Sales, Invoices, COGS, Gross Profit, Expenses, Net Profit, Receivables, Payables, Inventory Value
        """
        cursor = self.conn.cursor()
        date_clause = "DATE(sale_date) = DATE(?)" if target_date else "DATE(sale_date) = DATE('now', 'localtime')"
        params = [target_date] if target_date else []

        # 1. Sales Totals
        cursor.execute(f"""
            SELECT
                COUNT(id) as invoice_count,
                COALESCE(SUM(subtotal), 0) as total_subtotal,
                COALESCE(SUM(discount_amount), 0) as total_discounts,
                COALESCE(SUM(grand_total), 0) as total_revenue,
                COALESCE(SUM(paid_amount), 0) as total_cash_collected,
                COALESCE(SUM(balance_amount), 0) as total_credit_sales
            FROM sales
            WHERE {date_clause} AND is_returned = 0;
        """, params)
        s_row = cursor.fetchone()

        # 2. COGS & Returns
        cursor.execute(f"""
            SELECT
                COALESCE(SUM(si.quantity * si.cost_price), 0) as total_cogs
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE {date_clause} AND s.is_returned = 0;
        """, params)
        cogs_row = cursor.fetchone()
        cogs = to_decimal(cogs_row[0])

        # 3. Returns count and amount
        cursor.execute(f"""
            SELECT
                COUNT(id) as return_count,
                COALESCE(SUM(grand_total), 0) as total_returned
            FROM sales
            WHERE {date_clause} AND is_returned = 1;
        """, params)
        ret_row = cursor.fetchone()

        # 4. Expenses for the date
        exp_date_clause = "DATE(expense_date) = DATE(?)" if target_date else "DATE(expense_date) = DATE('now', 'localtime')"
        cursor.execute(f"SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE {exp_date_clause};", params)
        expenses = to_decimal(cursor.fetchone()[0])

        revenue = to_decimal(s_row["total_revenue"])
        gross_profit = revenue - cogs
        net_profit = gross_profit - expenses

        # 5. Customer outstanding receivables
        cursor.execute("SELECT COALESCE(SUM(current_balance), 0) FROM customers WHERE is_active = 1;")
        receivables = to_decimal(cursor.fetchone()[0])

        # 6. Supplier outstanding payables
        cursor.execute("SELECT COALESCE(SUM(current_balance), 0) FROM suppliers WHERE is_active = 1;")
        payables = to_decimal(cursor.fetchone()[0])

        # 7. Inventory total cost and count
        cursor.execute("""
            SELECT
                COALESCE(SUM(stock_quantity), 0) as qty,
                COALESCE(SUM(stock_quantity * cost_price), 0) as cost_val,
                COALESCE(SUM(stock_quantity * selling_price), 0) as retail_val
            FROM product_variants
            WHERE is_active = 1;
        """)
        inv_row = cursor.fetchone()

        # 8. Low stock alerts count
        cursor.execute("""
            SELECT COUNT(*) FROM product_variants v
            JOIN products p ON v.product_id = p.id
            WHERE v.stock_quantity <= p.min_stock_alert AND v.is_active = 1;
        """)
        low_stock_count = cursor.fetchone()[0]

        return {
            "invoice_count": s_row["invoice_count"],
            "total_revenue": revenue,
            "total_discounts": to_decimal(s_row["total_discounts"]),
            "cash_collected": to_decimal(s_row["total_cash_collected"]),
            "credit_sales": to_decimal(s_row["total_credit_sales"]),
            "cogs": cogs,
            "gross_profit": gross_profit,
            "expenses": expenses,
            "net_profit": net_profit,
            "returns_count": ret_row["return_count"],
            "returns_amount": to_decimal(ret_row["total_returned"]),
            "customer_receivables": receivables,
            "supplier_payables": payables,
            "inventory_units": to_qty_decimal(inv_row["qty"]),
            "inventory_cost_value": to_decimal(inv_row["cost_val"]),
            "inventory_retail_value": to_decimal(inv_row["retail_val"]),
            "low_stock_count": low_stock_count
        }

    def get_sales_by_category(self) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT c.name as category_name, c.name_urdu,
                   COUNT(si.id) as units_sold,
                   COALESCE(SUM(si.line_total), 0) as total_revenue
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.is_returned = 0
            GROUP BY c.id
            ORDER BY total_revenue DESC;
        """)
        return [dict(r) for r in cursor.fetchall()]

    def get_top_selling_products(self, limit: int = 10) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.name as product_name, p.code,
                   COALESCE(SUM(si.quantity), 0) as total_qty,
                   u.name as unit_name,
                   COALESCE(SUM(si.line_total), 0) as total_sales
            FROM sale_items si
            JOIN products p ON si.product_id = p.id
            JOIN units u ON p.unit_id = u.id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.is_returned = 0
            GROUP BY p.id
            ORDER BY total_sales DESC
            LIMIT ?;
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

    def get_recent_sales(self, limit: int = 25) -> List[dict]:
        """Returns recent sales invoices with customer details for dashboard table."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.id, s.invoice_number, s.sale_date, s.grand_total, s.paid_amount, s.balance_amount,
                   s.payment_method, s.is_revised, s.revision_count,
                   COALESCE(c.name, 'Walk-in Customer') as customer_name,
                   COALESCE(c.phone, '') as customer_phone
            FROM sales s
            LEFT JOIN customers c ON s.customer_id = c.id
            WHERE s.is_returned = 0
            ORDER BY s.id DESC
            LIMIT ?;
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]
