"""
Inventory Repository for Stock Adjustments, Purchases, Fabric Rolls, and Valuation
"""

import sqlite3
from typing import List, Optional, Dict
from decimal import Decimal
from app.models.entities import FabricRoll
from app.config import to_decimal, to_qty_decimal

class InventoryRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def set_opening_stock(self, variant_id: int, quantity: Decimal, cost_price: Decimal, user_id: int, notes: str = "Opening stock"):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE product_variants
            SET stock_quantity = ?, cost_price = ?
            WHERE id = ?;
        """, (float(quantity), float(cost_price), variant_id))

        cursor.execute("SELECT product_id FROM product_variants WHERE id = ?;", (variant_id,))
        prod_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO stock_transactions (
                product_id, variant_id, transaction_type, quantity, unit_cost, notes, user_id
            ) VALUES (?, ?, 'opening_stock', ?, ?, ?, ?);
        """, (prod_id, variant_id, float(quantity), float(cost_price), notes, user_id))
        self.conn.commit()

    def adjust_stock(
        self,
        variant_id: int,
        adjustment_qty: Optional[Decimal] = None,
        reason: str = "Stock adjustment",
        user_id: int = 1,
        new_quantity: Optional[Decimal] = None,
        product_id: Optional[int] = None,
        transaction_type: str = "adjustment",
        **kwargs
    ) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT product_id, stock_quantity, cost_price FROM product_variants WHERE id = ?;", (variant_id,))
        row = cursor.fetchone()
        if not row:
            return False
        db_prod_id, current_qty, cost = row[0], Decimal(str(row[1])), Decimal(str(row[2]))
        if product_id is None:
            product_id = db_prod_id

        if new_quantity is not None:
            delta = new_quantity - current_qty
            cursor.execute("UPDATE product_variants SET stock_quantity = ? WHERE id = ?;", (float(new_quantity), variant_id))
        else:
            delta = adjustment_qty if adjustment_qty is not None else Decimal("0.000")
            cursor.execute("UPDATE product_variants SET stock_quantity = stock_quantity + ? WHERE id = ?;", (float(delta), variant_id))

        cursor.execute("""
            INSERT INTO stock_transactions (
                product_id, variant_id, transaction_type, quantity, unit_cost, notes, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (product_id, variant_id, transaction_type, float(delta), float(cost), reason, user_id))
        self.conn.commit()
        return True

    def add_fabric_roll(self, roll: FabricRoll) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO fabric_rolls (
                product_id, variant_id, roll_number, initial_length, current_length, unit_name, cost_per_unit, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            roll.product_id,
            roll.variant_id,
            roll.roll_number,
            float(roll.initial_length),
            float(roll.current_length),
            roll.unit_name,
            float(roll.cost_per_unit),
            roll.notes
        ))
        roll_id = cursor.lastrowid
        # Also increment variant stock quantity by roll length
        if roll.variant_id:
            cursor.execute("""
                UPDATE product_variants
                SET stock_quantity = stock_quantity + ?
                WHERE id = ?;
            """, (float(roll.current_length), roll.variant_id))
        self.conn.commit()
        return roll_id

    def get_fabric_rolls_for_product(self, product_id: int, only_available: bool = True) -> List[FabricRoll]:
        cursor = self.conn.cursor()
        query = """
            SELECT id, product_id, variant_id, roll_number, initial_length, current_length, unit_name, cost_per_unit, status, notes
            FROM fabric_rolls
            WHERE product_id = ?
        """
        if only_available:
            query += " AND current_length > 0 AND status = 'active'"
        query += " ORDER BY id ASC;"
        cursor.execute(query, (product_id,))
        return [
            FabricRoll(
                id=r["id"],
                product_id=r["product_id"],
                variant_id=r["variant_id"],
                roll_number=r["roll_number"],
                initial_length=to_qty_decimal(r["initial_length"]),
                current_length=to_qty_decimal(r["current_length"]),
                unit_name=r["unit_name"],
                cost_per_unit=to_decimal(r["cost_per_unit"]),
                status=r["status"],
                notes=r["notes"]
            ) for r in cursor.fetchall()
        ]

    def get_low_stock_items(self) -> List[dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.name as product_name, p.code, v.id as variant_id, v.sku, v.size, v.color,
                   v.stock_quantity, p.min_stock_alert, u.name as unit_name
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            JOIN units u ON p.unit_id = u.id
            WHERE v.stock_quantity <= p.min_stock_alert AND v.is_active = 1
            ORDER BY v.stock_quantity ASC;
        """)
        return [dict(r) for r in cursor.fetchall()]

    def get_inventory_valuation(self) -> Dict[str, Decimal]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                SUM(stock_quantity) as total_qty,
                SUM(stock_quantity * cost_price) as total_cost,
                SUM(stock_quantity * selling_price) as total_retail
            FROM product_variants
            WHERE is_active = 1;
        """)
        r = cursor.fetchone()
        return {
            "total_items": to_qty_decimal(r[0] or 0),
            "total_cost_valuation": to_decimal(r[1] or 0),
            "total_retail_valuation": to_decimal(r[2] or 0)
        }

    def get_all_inventory_items(
        self,
        search: Optional[str] = None,
        category_id: Optional[int] = None,
        stock_filter: Optional[str] = None
    ) -> List[dict]:
        """Returns all items with stock level, unit cost, retail price, valuation, and alert status."""
        cursor = self.conn.cursor()
        query = """
            SELECT
                p.id as product_id,
                p.name as product_name,
                p.name_urdu,
                p.code as product_code,
                p.is_fabric,
                p.min_stock_alert,
                c.name as category_name,
                u.name as unit_name,
                u.symbol as unit_symbol,
                v.id as variant_id,
                v.sku,
                v.barcode,
                v.size,
                v.color,
                v.design,
                v.fabric_type,
                v.cost_price,
                v.selling_price,
                v.stock_quantity,
                (v.stock_quantity * v.cost_price) as cost_valuation,
                (v.stock_quantity * v.selling_price) as retail_valuation,
                v.is_active
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN units u ON p.unit_id = u.id
            WHERE v.is_active = 1 AND p.is_active = 1
        """
        params = []
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        if search:
            s = f"%{search.strip()}%"
            query += " AND (p.name LIKE ? OR p.name_urdu LIKE ? OR v.sku LIKE ? OR v.barcode LIKE ? OR v.size LIKE ?)"
            params.extend([s, s, s, s, s])

        if stock_filter == "low_stock":
            query += " AND v.stock_quantity <= p.min_stock_alert AND v.stock_quantity > 0"
        elif stock_filter == "out_of_stock":
            query += " AND v.stock_quantity <= 0"
        elif stock_filter == "in_stock":
            query += " AND v.stock_quantity > p.min_stock_alert"

        query += " ORDER BY p.name ASC, v.size ASC;"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["cost_price"] = to_decimal(d["cost_price"])
            d["selling_price"] = to_decimal(d["selling_price"])
            d["stock_quantity"] = to_qty_decimal(d["stock_quantity"])
            d["cost_valuation"] = to_decimal(d["cost_valuation"])
            d["retail_valuation"] = to_decimal(d["retail_valuation"])
            d["min_stock_alert"] = to_qty_decimal(d["min_stock_alert"])
            result.append(d)
        return result

    def get_stock_transactions(
        self,
        product_id: Optional[int] = None,
        variant_id: Optional[int] = None,
        limit: int = 200
    ) -> List[dict]:
        """Returns stock ledger history (sales deductions, purchases, manual adjustments, opening stock)."""
        cursor = self.conn.cursor()
        query = """
            SELECT
                st.id,
                st.created_at,
                st.transaction_type,
                st.quantity,
                st.unit_cost,
                st.notes,
                st.user_id,
                p.name as product_name,
                v.sku,
                v.size,
                v.color,
                u.full_name as user_name
            FROM stock_transactions st
            JOIN products p ON st.product_id = p.id
            LEFT JOIN product_variants v ON st.variant_id = v.id
            LEFT JOIN users u ON st.user_id = u.id
            WHERE 1=1
        """
        params = []
        if product_id:
            query += " AND st.product_id = ?"
            params.append(product_id)
        if variant_id:
            query += " AND st.variant_id = ?"
            params.append(variant_id)

        query += " ORDER BY st.id DESC LIMIT ?"
        params.append(limit)
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]

    def get_reorder_list(self) -> List[dict]:
        """Prepares a list of all products below minimum reorder alert threshold with recommended order quantities."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT
                p.name as product_name,
                p.code,
                v.id as variant_id,
                v.sku,
                v.size,
                v.color,
                v.cost_price,
                v.selling_price,
                v.stock_quantity,
                p.min_stock_alert,
                u.name as unit_name
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            JOIN units u ON p.unit_id = u.id
            WHERE v.stock_quantity <= p.min_stock_alert AND v.is_active = 1 AND p.is_active = 1
            ORDER BY (v.stock_quantity - p.min_stock_alert) ASC;
        """)
        items = []
        for r in cursor.fetchall():
            d = dict(r)
            curr = to_qty_decimal(d["stock_quantity"])
            min_a = to_qty_decimal(d["min_stock_alert"])
            rec = max(min_a * 2 - curr, Decimal("1.000"))
            d["current_stock"] = curr
            d["min_alert"] = min_a
            d["recommended_order"] = rec
            d["recommended_order_qty"] = rec
            items.append(d)
        return items

