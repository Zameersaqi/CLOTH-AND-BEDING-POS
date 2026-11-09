"""
Catalog Repository for Categories, Subcategories, Units, Products, and Variants
"""

import sqlite3
from typing import List, Optional
from decimal import Decimal
from app.models.entities import Category, Subcategory, Unit, Product, ProductVariant
from app.config import to_decimal, to_qty_decimal

class CatalogRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_categories(self, only_active: bool = True) -> List[Category]:
        cursor = self.conn.cursor()
        query = "SELECT id, code, name, name_urdu, description, display_order, is_active FROM categories"
        if only_active:
            query += " WHERE is_active = 1"
        query += " ORDER BY display_order ASC, name ASC"
        cursor.execute(query)
        rows = cursor.fetchall()
        return [
            Category(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                name_urdu=r["name_urdu"],
                description=r["description"],
                display_order=r["display_order"],
                is_active=bool(r["is_active"])
            ) for r in rows
        ]

    def get_subcategories(self, category_id: int, only_active: bool = True) -> List[Subcategory]:
        cursor = self.conn.cursor()
        query = "SELECT id, category_id, code, name, name_urdu, display_order, is_active FROM subcategories WHERE category_id = ?"
        if only_active:
            query += " AND is_active = 1"
        query += " ORDER BY display_order ASC, name ASC"
        cursor.execute(query, (category_id,))
        return [
            Subcategory(
                id=r["id"],
                category_id=r["category_id"],
                code=r["code"],
                name=r["name"],
                name_urdu=r["name_urdu"],
                display_order=r["display_order"],
                is_active=bool(r["is_active"])
            ) for r in cursor.fetchall()
        ]

    def get_units(self) -> List[Unit]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, code, name, is_decimal, symbol FROM units ORDER BY id ASC")
        return [
            Unit(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                is_decimal=bool(r["is_decimal"]),
                symbol=r["symbol"]
            ) for r in cursor.fetchall()
        ]

    def get_products(
        self,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        search_term: Optional[str] = None,
        only_active: bool = True
    ) -> List[Product]:
        cursor = self.conn.cursor()
        query = """
            SELECT p.id, p.category_id, p.subcategory_id, p.code, p.barcode, p.name, p.name_urdu,
                   p.unit_id, p.is_template, p.is_fabric, p.min_stock_alert, p.base_cost_price,
                   p.base_selling_price, p.description, p.image_path, p.is_active,
                   u.name as unit_name, c.name as category_name
            FROM products p
            JOIN units u ON p.unit_id = u.id
            JOIN categories c ON p.category_id = c.id
            WHERE 1=1
        """
        params = []
        if only_active:
            query += " AND p.is_active = 1"
        if category_id:
            query += " AND p.category_id = ?"
            params.append(category_id)
        if subcategory_id:
            query += " AND p.subcategory_id = ?"
            params.append(subcategory_id)
        if search_term:
            term = f"%{search_term.strip()}%"
            query += " AND (p.name LIKE ? OR p.code LIKE ? OR p.barcode LIKE ? OR p.name_urdu LIKE ?)"
            params.extend([term, term, term, term])

        query += " ORDER BY c.display_order ASC, p.id ASC"
        cursor.execute(query, params)
        rows = cursor.fetchall()

        products = []
        for r in rows:
            prod = Product(
                id=r["id"],
                category_id=r["category_id"],
                subcategory_id=r["subcategory_id"],
                code=r["code"],
                barcode=r["barcode"],
                name=r["name"],
                name_urdu=r["name_urdu"],
                unit_id=r["unit_id"],
                is_template=bool(r["is_template"]),
                is_fabric=bool(r["is_fabric"]),
                min_stock_alert=to_qty_decimal(r["min_stock_alert"]),
                base_cost_price=to_decimal(r["base_cost_price"]),
                base_selling_price=to_decimal(r["base_selling_price"]),
                description=r["description"],
                image_path=r["image_path"],
                is_active=bool(r["is_active"]),
                unit_name=r["unit_name"],
                category_name=r["category_name"],
                variants=[]
            )
            prod.variants = self.get_variants_for_product(prod.id)
            products.append(prod)

        return products

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        cursor = self.conn.cursor()
        query = """
            SELECT p.id, p.category_id, p.subcategory_id, p.code, p.barcode, p.name, p.name_urdu,
                   p.unit_id, p.is_template, p.is_fabric, p.min_stock_alert, p.base_cost_price,
                   p.base_selling_price, p.description, p.image_path, p.is_active,
                   u.name as unit_name, c.name as category_name
            FROM products p
            JOIN units u ON p.unit_id = u.id
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = ?
        """
        cursor.execute(query, (product_id,))
        r = cursor.fetchone()
        if not r:
            return None
        prod = Product(
            id=r["id"],
            category_id=r["category_id"],
            subcategory_id=r["subcategory_id"],
            code=r["code"],
            barcode=r["barcode"],
            name=r["name"],
            name_urdu=r["name_urdu"],
            unit_id=r["unit_id"],
            is_template=bool(r["is_template"]),
            is_fabric=bool(r["is_fabric"]),
            min_stock_alert=to_qty_decimal(r["min_stock_alert"]),
            base_cost_price=to_decimal(r["base_cost_price"]),
            base_selling_price=to_decimal(r["base_selling_price"]),
            description=r["description"],
            image_path=r["image_path"],
            is_active=bool(r["is_active"]),
            unit_name=r["unit_name"],
            category_name=r["category_name"],
            variants=[]
        )
        prod.variants = self.get_variants_for_product(prod.id)
        return prod

    def get_variants_for_product(self, product_id: int, only_active: bool = True) -> List[ProductVariant]:
        cursor = self.conn.cursor()
        query = """
            SELECT id, product_id, sku, barcode, size, color, design, fabric_type,
                   dimensions, weight_grams, cost_price, selling_price, stock_quantity, is_active
            FROM product_variants
            WHERE product_id = ?
        """
        if only_active:
            query += " AND is_active = 1"
        query += " ORDER BY id ASC"
        cursor.execute(query, (product_id,))
        return [
            ProductVariant(
                id=r["id"],
                product_id=r["product_id"],
                sku=r["sku"],
                barcode=r["barcode"],
                size=r["size"],
                color=r["color"],
                design=r["design"],
                fabric_type=r["fabric_type"],
                dimensions=r["dimensions"],
                weight_grams=r["weight_grams"],
                cost_price=to_decimal(r["cost_price"]),
                selling_price=to_decimal(r["selling_price"]),
                stock_quantity=to_qty_decimal(r["stock_quantity"]),
                is_active=bool(r["is_active"])
            ) for r in cursor.fetchall()
        ]

    def find_by_barcode(self, barcode: str) -> Optional[dict]:
        """Looks up a product or variant directly by barcode or SKU for rapid POS scanning."""
        cursor = self.conn.cursor()
        # 1. Search in variants first
        cursor.execute("""
            SELECT v.id as variant_id, v.product_id, v.sku, v.size, v.color, v.selling_price, v.cost_price,
                   p.name as product_name, p.is_fabric, u.name as unit_name, u.is_decimal
            FROM product_variants v
            JOIN products p ON v.product_id = p.id
            JOIN units u ON p.unit_id = u.id
            WHERE v.barcode = ? OR v.sku = ?
            LIMIT 1
        """, (barcode, barcode))
        r = cursor.fetchone()
        if r:
            return dict(r)

        # 2. Search in products
        cursor.execute("""
            SELECT NULL as variant_id, p.id as product_id, p.code as sku, NULL as size, NULL as color,
                   p.base_selling_price as selling_price, p.base_cost_price as cost_price,
                   p.name as product_name, p.is_fabric, u.name as unit_name, u.is_decimal
            FROM products p
            JOIN units u ON p.unit_id = u.id
            WHERE p.barcode = ? OR p.code = ?
            LIMIT 1
        """, (barcode, barcode))
        r2 = cursor.fetchone()
        if r2:
            return dict(r2)
        return None

    def update_variant_pricing_stock(self, variant_id: int, cost: Decimal, price: Decimal, stock: Decimal):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE product_variants
            SET cost_price = ?, selling_price = ?, stock_quantity = ?
            WHERE id = ?;
        """, (float(cost), float(price), float(stock), variant_id))
        self.conn.commit()
