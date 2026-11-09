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

    def adjust_stock(self, variant_id: int, adjustment_qty: Decimal, reason: str, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE product_variants
            SET stock_quantity = stock_quantity + ?
            WHERE id = ?;
        """, (float(adjustment_qty), variant_id))

        cursor.execute("SELECT product_id, cost_price FROM product_variants WHERE id = ?;", (variant_id,))
        row = cursor.fetchone()
        prod_id, cost = row[0], row[1]

        cursor.execute("""
            INSERT INTO stock_transactions (
                product_id, variant_id, transaction_type, quantity, unit_cost, notes, user_id
            ) VALUES (?, ?, 'adjustment', ?, ?, ?, ?);
        """, (prod_id, variant_id, float(adjustment_qty), cost, reason, user_id))
        self.conn.commit()

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
