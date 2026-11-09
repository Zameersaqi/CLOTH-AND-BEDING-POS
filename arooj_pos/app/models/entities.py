"""
Domain Entities and Data Classes for Arooj POS
Uses standard Decimal types for monetary amounts to guarantee exact precision.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, List
from app.config import to_decimal, to_qty_decimal

@dataclass
class Category:
    id: Optional[int]
    code: str
    name: str
    name_urdu: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True

@dataclass
class Subcategory:
    id: Optional[int]
    category_id: int
    code: str
    name: str
    name_urdu: Optional[str] = None
    display_order: int = 0
    is_active: bool = True

@dataclass
class Unit:
    id: Optional[int]
    code: str
    name: str
    is_decimal: bool
    symbol: str

@dataclass
class ProductVariant:
    id: Optional[int]
    product_id: int
    sku: str
    barcode: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    design: Optional[str] = None
    fabric_type: Optional[str] = None
    dimensions: Optional[str] = None
    weight_grams: Optional[float] = None
    cost_price: Decimal = Decimal("0.00")
    selling_price: Decimal = Decimal("0.00")
    stock_quantity: Decimal = Decimal("0.000")
    is_active: bool = True

    def display_title(self) -> str:
        parts = [p for p in [self.size, self.color, self.design, self.fabric_type] if p]
        return " - ".join(parts) if parts else "Standard"

@dataclass
class Product:
    id: Optional[int]
    category_id: int
    subcategory_id: Optional[int]
    code: str
    barcode: Optional[str]
    name: str
    unit_id: int
    name_urdu: Optional[str] = None
    is_template: bool = False
    is_fabric: bool = False
    min_stock_alert: Decimal = Decimal("5.000")
    base_cost_price: Decimal = Decimal("0.00")
    base_selling_price: Decimal = Decimal("0.00")
    description: Optional[str] = None
    image_path: Optional[str] = None
    is_active: bool = True
    unit_name: Optional[str] = "Pcs"
    category_name: Optional[str] = ""
    variants: List[ProductVariant] = field(default_factory=list)

    @property
    def cost_price(self) -> Decimal:
        return self.base_cost_price

    @property
    def sale_price(self) -> Decimal:
        return self.base_selling_price

@dataclass
class FabricRoll:
    id: Optional[int]
    product_id: int
    variant_id: Optional[int]
    roll_number: str
    initial_length: Decimal
    current_length: Decimal
    unit_name: str = "Meter"
    cost_per_unit: Decimal = Decimal("0.00")
    status: str = "active"
    notes: Optional[str] = None

@dataclass
class Customer:
    id: Optional[int]
    code: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: str = "Local"
    credit_limit: Decimal = Decimal("50000.00")
    opening_balance: Decimal = Decimal("0.00")
    current_balance: Decimal = Decimal("0.00")
    discount_percent: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    is_active: bool = True

@dataclass
class Supplier:
    id: Optional[int]
    code: str
    company_name: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    opening_balance: Decimal = Decimal("0.00")
    current_balance: Decimal = Decimal("0.00")
    notes: Optional[str] = None
    is_active: bool = True

@dataclass
class CartItem:
    product_id: int
    product_name: str
    variant_id: Optional[int] = None
    variant_title: str = "Standard"
    sku: str = ""
    unit_name: str = "Pcs"
    is_decimal: bool = False
    is_fabric: bool = False
    quantity: Decimal = Decimal("1.000")
    original_catalog_price: Decimal = Decimal("0.00")
    transaction_price: Decimal = Decimal("0.00")  # Editable by cashier/manager
    line_discount: Decimal = Decimal("0.00")
    cost_price: Decimal = Decimal("0.00")
    is_price_overridden: bool = False
    override_reason: Optional[str] = None
    override_approved_by: Optional[str] = None
    roll_id: Optional[int] = None
    roll_number: Optional[str] = None

    @property
    def line_subtotal(self) -> Decimal:
        return to_decimal(self.quantity * self.transaction_price)

    @property
    def line_total(self) -> Decimal:
        return to_decimal(self.line_subtotal - self.line_discount)

@dataclass
class Sale:
    id: Optional[int]
    invoice_number: str
    customer_id: Optional[int]
    cashier_id: Optional[int]
    sale_date: str
    subtotal: Decimal
    discount_amount: Decimal
    discount_percent: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    paid_amount: Decimal
    balance_amount: Decimal
    payment_status: str  # 'paid', 'partial', 'unpaid'
    payment_method: str  # 'Cash', 'Credit', 'Card', 'Split'
    notes: Optional[str] = None
    is_returned: bool = False
    return_ref_id: Optional[int] = None
    items: List[CartItem] = field(default_factory=list)

@dataclass
class User:
    id: Optional[int]
    username: str
    full_name: str
    role: str  # 'admin', 'manager', 'cashier', 'inventory'
    password_hash: str
    salt: str
    manager_pin: Optional[str] = None
    is_active: bool = True

@dataclass
class Expense:
    category: str = "General"
    amount: Decimal = Decimal("0.00")
    id: Optional[int] = None
    payment_method: str = "Cash"
    description: Optional[str] = None
    receipt_ref: Optional[str] = None
    recorded_by: Optional[int] = None
    expense_date: Optional[str] = None
    user_id: Optional[int] = None
    reference_number: Optional[str] = None

    def __post_init__(self):
        if self.user_id is not None and self.recorded_by is None:
            self.recorded_by = self.user_id
        if self.reference_number is not None and self.receipt_ref is None:
            self.receipt_ref = self.reference_number
