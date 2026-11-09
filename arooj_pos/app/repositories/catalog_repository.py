"""
Catalog Repository for Categories, Subcategories, Units, Products, and Variants
"""

import sqlite3
from typing import List, Optional, Union, Dict, Any
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

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, code, name, name_urdu, description, display_order, is_active FROM categories WHERE id = ?", (category_id,))
        r = cursor.fetchone()
        if not r:
            return None
        return Category(
            id=r["id"],
            code=r["code"],
            name=r["name"],
            name_urdu=r["name_urdu"],
            description=r["description"],
            display_order=r["display_order"],
            is_active=bool(r["is_active"])
        )

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

    def get_product_by_barcode(self, barcode: str):
        """Helper to look up product variant by barcode or SKU."""
        r = self.find_by_barcode(barcode)
        if not r:
            return None
        class FoundItem:
            def __init__(self, d):
                self.product_name = d["product_name"]
                self.selling_price = to_decimal(d["selling_price"])
                self.purchase_price = to_decimal(d["cost_price"])
                self.cost_price = self.purchase_price
                self.sku = d.get("sku")
        return FoundItem(r)

    def update_variant_pricing_stock(self, variant_id: int, cost: Decimal, price: Decimal, stock: Decimal):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE product_variants
            SET cost_price = ?, selling_price = ?, stock_quantity = ?
            WHERE id = ?;
        """, (float(cost), float(price), float(stock), variant_id))
        self.conn.commit()

    def sku_exists(self, sku: str, exclude_product_id: Optional[int] = None, exclude_variant_id: Optional[int] = None) -> bool:
        if not sku or not sku.strip():
            return False
        val = sku.strip()
        cursor = self.conn.cursor()
        # Check products
        q1 = "SELECT id FROM products WHERE code = ?"
        p1 = [val]
        if exclude_product_id:
            q1 += " AND id != ?"
            p1.append(exclude_product_id)
        cursor.execute(q1, p1)
        if cursor.fetchone():
            return True

        # Check variants
        q2 = "SELECT id FROM product_variants WHERE sku = ?"
        p2 = [val]
        if exclude_variant_id:
            q2 += " AND id != ?"
            p2.append(exclude_variant_id)
        cursor.execute(q2, p2)
        return cursor.fetchone() is not None

    def barcode_exists(self, barcode: str, exclude_product_id: Optional[int] = None, exclude_variant_id: Optional[int] = None) -> bool:
        if not barcode or not barcode.strip():
            return False
        val = barcode.strip()
        cursor = self.conn.cursor()
        # Check products
        q1 = "SELECT id FROM products WHERE barcode = ?"
        p1 = [val]
        if exclude_product_id:
            q1 += " AND id != ?"
            p1.append(exclude_product_id)
        cursor.execute(q1, p1)
        if cursor.fetchone():
            return True

        # Check variants
        q2 = "SELECT id FROM product_variants WHERE barcode = ?"
        p2 = [val]
        if exclude_variant_id:
            q2 += " AND id != ?"
            p2.append(exclude_variant_id)
        cursor.execute(q2, p2)
        return cursor.fetchone() is not None

    def generate_unique_sku(self, prefix: str = "PRD", category_id: Optional[int] = None) -> str:
        if category_id:
            cat = self.get_category_by_id(category_id)
            if cat and cat.code:
                prefix = cat.code
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM products;")
        max_id = (cursor.fetchone()[0] or 0) + 1
        sku = f"{prefix}-{max_id:04d}"
        seq = max_id
        while self.sku_exists(sku):
            seq += 1
            sku = f"{prefix}-{seq:04d}"
        return sku

    def generate_unique_barcode(self, prefix: str = "200") -> str:
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(id) FROM product_variants;")
        max_vid = (cursor.fetchone()[0] or 0) + 1
        cursor.execute("SELECT MAX(id) FROM products;")
        max_pid = (cursor.fetchone()[0] or 0) + 1
        num = max(max_vid, max_pid) + 1000

        # Create 12-digit numeric barcode
        candidate = f"{prefix}{num:09d}"
        seq = num
        while self.barcode_exists(candidate):
            seq += 1
            candidate = f"{prefix}{seq:09d}"
        return candidate

    def create_product(
        self,
        category_id: Union[int, dict] = 1,
        subcategory_id: Optional[int] = None,
        code: str = "",
        barcode: Optional[str] = None,
        name: str = "",
        name_urdu: Optional[str] = None,
        unit_id: int = 1,
        is_template: bool = False,
        is_fabric: bool = False,
        min_stock_alert: Decimal = Decimal("5.000"),
        base_cost_price: Decimal = Decimal("0.00"),
        base_selling_price: Decimal = Decimal("0.00"),
        description: Optional[str] = None,
        opening_stock: Decimal = Decimal("0.000"),
        is_active: bool = True,
        user_id: int = 1,
        **kwargs
    ) -> int:
        if isinstance(category_id, dict):
            d = category_id
            user_id = subcategory_id if isinstance(subcategory_id, int) else d.get("user_id", 1)
            cat_val = d.get("category_id", 1)
            subcategory_id = d.get("subcategory_id")
            code = d.get("code") or d.get("sku") or ""
            barcode = d.get("barcode")
            name = d.get("name", "")
            name_urdu = d.get("name_urdu")
            unit_id = d.get("unit_id", 1)
            nature = d.get("product_nature", "")
            is_template = bool(d.get("is_template", nature == "variant"))
            is_fabric = bool(d.get("is_fabric", nature == "fabric"))
            min_stock_alert = to_qty_decimal(d.get("min_stock_alert", 5))
            base_cost_price = to_decimal(d.get("base_cost_price", d.get("cost_price", 0)))
            base_selling_price = to_decimal(d.get("base_selling_price", d.get("sale_price", 0)))
            description = d.get("description")
            opening_stock = to_qty_decimal(d.get("opening_stock", 0))
            is_active = bool(d.get("is_active", True))
            category_id = cat_val

        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO products (
                category_id, subcategory_id, code, barcode, name, name_urdu, unit_id,
                is_template, is_fabric, min_stock_alert, base_cost_price, base_selling_price,
                description, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            category_id,
            subcategory_id,
            code.strip(),
            barcode.strip() if barcode and barcode.strip() else None,
            name.strip(),
            name_urdu.strip() if name_urdu and name_urdu.strip() else None,
            unit_id,
            1 if is_template else 0,
            1 if is_fabric else 0,
            float(min_stock_alert),
            float(base_cost_price),
            float(base_selling_price),
            description.strip() if description and description.strip() else None,
            1 if is_active else 0
        ))
        product_id = cursor.lastrowid

        # If standard product (not variant template), automatically create a default variant
        if not is_template:
            cursor.execute("""
                INSERT INTO product_variants (
                    product_id, sku, barcode, size, color, design, fabric_type,
                    cost_price, selling_price, stock_quantity, is_active
                ) VALUES (?, ?, ?, 'Standard', NULL, NULL, NULL, ?, ?, ?, ?);
            """, (
                product_id,
                code.strip(),
                barcode.strip() if barcode and barcode.strip() else None,
                float(base_cost_price),
                float(base_selling_price),
                float(opening_stock),
                1 if is_active else 0
            ))
            variant_id = cursor.lastrowid

            if opening_stock > Decimal("0.000"):
                cursor.execute("""
                    INSERT INTO stock_transactions (
                        product_id, variant_id, transaction_type, quantity, unit_cost, notes, user_id
                    ) VALUES (?, ?, 'opening_stock', ?, ?, 'Initial opening stock on product creation', ?);
                """, (product_id, variant_id, float(opening_stock), float(base_cost_price), user_id))

        self.conn.commit()
        return product_id

    def update_product(
        self,
        product_id: int,
        category_id: Union[int, dict] = 1,
        subcategory_id: Optional[int] = None,
        code: str = "",
        barcode: Optional[str] = None,
        name: str = "",
        name_urdu: Optional[str] = None,
        unit_id: int = 1,
        is_fabric: bool = False,
        min_stock_alert: Decimal = Decimal("5.000"),
        base_cost_price: Decimal = Decimal("0.00"),
        base_selling_price: Decimal = Decimal("0.00"),
        description: Optional[str] = None,
        is_active: bool = True,
        stock_quantity: Optional[Decimal] = None,
        **kwargs
    ) -> bool:
        if isinstance(category_id, dict):
            d = category_id
            cat_val = d.get("category_id", 1)
            subcategory_id = d.get("subcategory_id")
            code = d.get("code") or d.get("sku") or ""
            barcode = d.get("barcode")
            name = d.get("name", "")
            name_urdu = d.get("name_urdu")
            unit_id = d.get("unit_id", 1)
            nature = d.get("product_nature", "")
            is_fabric = bool(d.get("is_fabric", nature == "fabric"))
            min_stock_alert = to_qty_decimal(d.get("min_stock_alert", 5))
            base_cost_price = to_decimal(d.get("base_cost_price", d.get("cost_price", 0)))
            base_selling_price = to_decimal(d.get("base_selling_price", d.get("sale_price", 0)))
            description = d.get("description")
            is_active = bool(d.get("is_active", True))
            stock_quantity = to_qty_decimal(d["stock_quantity"]) if "stock_quantity" in d and d["stock_quantity"] is not None else None
            category_id = cat_val

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE products
            SET category_id = ?, subcategory_id = ?, code = ?, barcode = ?,
                name = ?, name_urdu = ?, unit_id = ?, is_fabric = ?,
                min_stock_alert = ?, base_cost_price = ?, base_selling_price = ?,
                description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (
            category_id,
            subcategory_id,
            code.strip(),
            barcode.strip() if barcode and barcode.strip() else None,
            name.strip(),
            name_urdu.strip() if name_urdu and name_urdu.strip() else None,
            unit_id,
            1 if is_fabric else 0,
            float(min_stock_alert),
            float(base_cost_price),
            float(base_selling_price),
            description.strip() if description and description.strip() else None,
            1 if is_active else 0,
            product_id
        ))

        # Check if product is standard (has only 1 default variant)
        cursor.execute("SELECT id, size FROM product_variants WHERE product_id = ?;", (product_id,))
        variants = cursor.fetchall()
        if len(variants) == 1:
            var_id = variants[0]["id"]
            if stock_quantity is not None:
                cursor.execute("""
                    UPDATE product_variants
                    SET sku = ?, barcode = ?, cost_price = ?, selling_price = ?, stock_quantity = ?, is_active = ?
                    WHERE id = ?;
                """, (
                    code.strip(),
                    barcode.strip() if barcode and barcode.strip() else None,
                    float(base_cost_price),
                    float(base_selling_price),
                    float(stock_quantity),
                    1 if is_active else 0,
                    var_id
                ))
            else:
                cursor.execute("""
                    UPDATE product_variants
                    SET sku = ?, barcode = ?, cost_price = ?, selling_price = ?, is_active = ?
                    WHERE id = ?;
                """, (
                    code.strip(),
                    barcode.strip() if barcode and barcode.strip() else None,
                    float(base_cost_price),
                    float(base_selling_price),
                    1 if is_active else 0,
                    var_id
                ))

        self.conn.commit()
        return True

    def deactivate_product(self, product_id: int):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE products SET is_active = 0 WHERE id = ?;", (product_id,))
        cursor.execute("UPDATE product_variants SET is_active = 0 WHERE product_id = ?;", (product_id,))
        self.conn.commit()

    def activate_product(self, product_id: int):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE products SET is_active = 1 WHERE id = ?;", (product_id,))
        cursor.execute("UPDATE product_variants SET is_active = 1 WHERE product_id = ?;", (product_id,))
        self.conn.commit()

    def create_variant(
        self,
        product_id: Union[int, dict] = 1,
        sku: str = "",
        barcode: Optional[str] = None,
        size: Optional[str] = None,
        color: Optional[str] = None,
        design: Optional[str] = None,
        fabric_type: Optional[str] = None,
        cost_price: Decimal = Decimal("0.00"),
        selling_price: Decimal = Decimal("0.00"),
        stock_quantity: Decimal = Decimal("0.000"),
        dimensions: Optional[str] = None,
        weight_grams: Optional[float] = None,
        is_active: bool = True,
        user_id: int = 1,
        **kwargs
    ) -> int:
        if isinstance(product_id, dict):
            d = product_id
            user_id = sku if isinstance(sku, int) else d.get("user_id", 1)
            p_val = d.get("product_id", 1)
            sku = d.get("sku", "")
            barcode = d.get("barcode")
            size = d.get("size")
            color = d.get("color")
            design = d.get("design")
            fabric_type = d.get("fabric_type")
            cost_price = to_decimal(d.get("cost_price", 0))
            selling_price = to_decimal(d.get("selling_price", d.get("sale_price", 0)))
            stock_quantity = to_qty_decimal(d.get("stock_quantity", 0))
            dimensions = d.get("dimensions")
            weight_grams = d.get("weight_grams")
            is_active = bool(d.get("is_active", True))
            product_id = p_val

        cursor = self.conn.cursor()
        # Mark product as template if creating extra variants
        cursor.execute("UPDATE products SET is_template = 1 WHERE id = ?;", (product_id,))

        cursor.execute("""
            INSERT INTO product_variants (
                product_id, sku, barcode, size, color, design, fabric_type,
                dimensions, weight_grams, cost_price, selling_price, stock_quantity, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            product_id,
            sku.strip(),
            barcode.strip() if barcode and barcode.strip() else None,
            size.strip() if size and size.strip() else None,
            color.strip() if color and color.strip() else None,
            design.strip() if design and design.strip() else None,
            fabric_type.strip() if fabric_type and fabric_type.strip() else None,
            dimensions.strip() if dimensions and dimensions.strip() else None,
            weight_grams,
            float(cost_price),
            float(selling_price),
            float(stock_quantity),
            1 if is_active else 0
        ))
        variant_id = cursor.lastrowid

        if stock_quantity > Decimal("0.000"):
            cursor.execute("""
                INSERT INTO stock_transactions (
                    product_id, variant_id, transaction_type, quantity, unit_cost, notes, user_id
                ) VALUES (?, ?, 'opening_stock', ?, ?, 'Initial opening stock on variant creation', ?);
            """, (product_id, variant_id, float(stock_quantity), float(cost_price), user_id))

        self.conn.commit()
        return variant_id

    def update_variant(
        self,
        variant_id: int,
        sku: Union[str, dict] = "",
        barcode: Optional[str] = None,
        size: Optional[str] = None,
        color: Optional[str] = None,
        design: Optional[str] = None,
        fabric_type: Optional[str] = None,
        cost_price: Decimal = Decimal("0.00"),
        selling_price: Decimal = Decimal("0.00"),
        stock_quantity: Decimal = Decimal("0.000"),
        dimensions: Optional[str] = None,
        is_active: bool = True,
        **kwargs
    ) -> bool:
        if isinstance(sku, dict):
            d = sku
            sku_val = d.get("sku", "")
            barcode = d.get("barcode")
            size = d.get("size")
            color = d.get("color")
            design = d.get("design")
            fabric_type = d.get("fabric_type")
            cost_price = to_decimal(d.get("cost_price", 0))
            selling_price = to_decimal(d.get("selling_price", d.get("sale_price", 0)))
            stock_quantity = to_qty_decimal(d.get("stock_quantity", 0))
            dimensions = d.get("dimensions")
            is_active = bool(d.get("is_active", True))
            sku = sku_val

        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE product_variants
            SET sku = ?, barcode = ?, size = ?, color = ?, design = ?, fabric_type = ?,
                dimensions = ?, cost_price = ?, selling_price = ?, stock_quantity = ?, is_active = ?
            WHERE id = ?;
        """, (
            sku.strip(),
            barcode.strip() if barcode and barcode.strip() else None,
            size.strip() if size and size.strip() else None,
            color.strip() if color and color.strip() else None,
            design.strip() if design and design.strip() else None,
            fabric_type.strip() if fabric_type and fabric_type.strip() else None,
            dimensions.strip() if dimensions and dimensions.strip() else None,
            float(cost_price),
            float(selling_price),
            float(stock_quantity),
            1 if is_active else 0,
            variant_id
        ))
        self.conn.commit()
        return True

    def deactivate_variant(self, variant_id: int):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE product_variants SET is_active = 0 WHERE id = ?;", (variant_id,))
        self.conn.commit()

