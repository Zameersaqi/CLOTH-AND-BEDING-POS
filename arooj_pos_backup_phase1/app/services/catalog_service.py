"""
Catalog, Customer, and Inventory Services for Arooj POS
"""

from typing import List, Optional
from decimal import Decimal
from app.models.entities import Category, Product, ProductVariant, Customer, FabricRoll
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.inventory_repository import InventoryRepository

class CatalogService:
    def __init__(self, catalog_repo: CatalogRepository):
        self.catalog_repo = catalog_repo

    def get_categories(self) -> List[Category]:
        return self.catalog_repo.get_categories(only_active=True)

    def get_products(self, category_id: Optional[int] = None, search: Optional[str] = None) -> List[Product]:
        return self.catalog_repo.get_products(category_id=category_id, search_term=search)

    def activate_template_product(self, product_id: int, selling_price: Decimal, cost_price: Decimal, opening_stock: Decimal):
        """Allows the shop owner to convert an initial catalog template into a real stocked product."""
        prod = self.catalog_repo.get_product_by_id(product_id)
        if prod:
            cursor = self.catalog_repo.conn.cursor()
            cursor.execute("UPDATE products SET is_template = 0, base_selling_price = ?, base_cost_price = ? WHERE id = ?;", (float(selling_price), float(cost_price), product_id))
            # If product has variants, update first variant
            if prod.variants:
                v = prod.variants[0]
                cursor.execute("UPDATE product_variants SET selling_price = ?, cost_price = ?, stock_quantity = ? WHERE id = ?;", (float(selling_price), float(cost_price), float(opening_stock), v.id))
            self.catalog_repo.conn.commit()

class CustomerService:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    def get_customers(self, search: Optional[str] = None) -> List[Customer]:
        return self.customer_repo.get_all(search)

    def record_payment(self, customer_id: int, amount: Decimal, payment_method: str = "Cash", notes: str = "") -> Decimal:
        return self.customer_repo.receive_payment(customer_id, amount, payment_method, notes)

class InventoryService:
    def __init__(self, inv_repo: InventoryRepository):
        self.inv_repo = inv_repo

    def adjust_stock(self, variant_id: int, adjustment_qty: Decimal, reason: str, user_id: int):
        self.inv_repo.adjust_stock(variant_id, adjustment_qty, reason, user_id)

    def register_fabric_roll(self, roll: FabricRoll) -> int:
        return self.inv_repo.add_fabric_roll(roll)
