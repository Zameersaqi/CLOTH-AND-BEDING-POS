"""
Sales Service: Heart of POS Cart Operations, Negotiated Price Overrides, and Checkout
Strictly enforces Part 6 & Part 7 rules:
- Transaction prices in cart are editable without altering master catalog prices
- Enforces discount thresholds and Manager PIN verification
- Calculates exact Decimal financials without floating point rounding errors
- Atomic sale recording and stock deduction
"""

from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from app.models.entities import CartItem, Sale, Product, ProductVariant, FabricRoll, User
from app.repositories.sales_repository import SalesRepository
from app.repositories.user_repository import UserRepository
from app.repositories.settings_repository import SettingsRepository
from app.config import to_decimal, to_qty_decimal

class SalesService:
    def __init__(
        self,
        sales_repo: SalesRepository,
        user_repo: UserRepository,
        settings_repo: SettingsRepository
    ):
        self.sales_repo = sales_repo
        self.user_repo = user_repo
        self.settings_repo = settings_repo

    def add_to_cart(
        self,
        cart: List[CartItem],
        product: Product,
        variant: Optional[ProductVariant] = None,
        quantity: Decimal = Decimal("1.000"),
        fabric_roll: Optional[FabricRoll] = None
    ) -> List[CartItem]:
        """
        Adds an item to the cart or increments existing matching item.
        If variant has price, uses it; otherwise uses product base_selling_price.
        """
        var_id = variant.id if variant else None
        sku = variant.sku if variant else product.code
        title = variant.display_title() if variant else "Standard"

        # Catalog master price (read-only reference)
        catalog_price = variant.selling_price if (variant and variant.selling_price > 0) else product.base_selling_price
        cost_price = variant.cost_price if (variant and variant.cost_price > 0) else product.base_cost_price

        roll_id = fabric_roll.id if fabric_roll else None
        roll_num = fabric_roll.roll_number if fabric_roll else None

        # Check if already in cart (same variant and roll)
        for existing in cart:
            if existing.product_id == product.id and existing.variant_id == var_id and existing.roll_id == roll_id:
                existing.quantity = to_qty_decimal(existing.quantity + quantity)
                return cart

        # Add new item
        item = CartItem(
            product_id=product.id,
            product_name=product.name,
            variant_id=var_id,
            variant_title=title,
            sku=sku,
            unit_name=product.unit_name or "Pcs",
            is_decimal=product.is_fabric,
            is_fabric=product.is_fabric,
            quantity=to_qty_decimal(quantity),
            original_catalog_price=to_decimal(catalog_price),
            transaction_price=to_decimal(catalog_price),  # Initial price equals catalog price
            cost_price=to_decimal(cost_price),
            roll_id=roll_id,
            roll_number=roll_num
        )
        cart.append(item)
        return cart

    def update_cart_item_price(
        self,
        item: CartItem,
        new_transaction_price: Decimal,
        current_user: Optional[User] = None,
        manager_pin: Optional[str] = None,
        override_reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Enforces Part 6:
        - Changes only item.transaction_price, NEVER the master catalog price.
        - Verifies that new price is non-negative.
        - Calculates discount from original catalog price.
        - If discount exceeds configured max_cashier_discount_percent, requires manager PIN.
        - Records reason and approved_by.
        """
        new_price = to_decimal(new_transaction_price)
        if new_price < Decimal("0.00"):
            return False, "Price cannot be negative."

        orig_price = item.original_catalog_price

        # Check discount percentage
        if orig_price > Decimal("0.00") and new_price < orig_price:
            discount_amount = orig_price - new_price
            discount_percent = (discount_amount / orig_price) * Decimal("100.00")
            max_allowed_str = self.settings_repo.get_setting("max_cashier_discount_percent", "10.0")
            try:
                max_allowed = Decimal(max_allowed_str)
            except Exception:
                max_allowed = Decimal("10.0")

            # Cashier discount check
            user_role = current_user.role if current_user else "cashier"
            if user_role not in ("admin", "manager") and discount_percent > max_allowed:
                if not manager_pin or not self.user_repo.verify_manager_pin(manager_pin):
                    return False, f"Price reduction of {discount_percent:.1f}% exceeds cashier limit ({max_allowed}%). Valid Manager PIN required."
                item.override_approved_by = "Manager Authorized"

        # Apply price override
        item.transaction_price = new_price
        if new_price != orig_price:
            item.is_price_overridden = True
            item.override_reason = override_reason or "Customer negotiation at counter"
            if not item.override_approved_by:
                item.override_approved_by = current_user.username if current_user else "Cashier"

            # Audit log
            user_id = current_user.id if current_user else None
            self.user_repo.log_audit(
                user_id=user_id,
                action="PRICE_OVERRIDE",
                entity="cart_item",
                entity_id=item.sku,
                details=f"Item {item.product_name} ({item.sku}) price overridden from {orig_price} to {new_price}. Reason: {item.override_reason}"
            )
        else:
            item.is_price_overridden = False
            item.override_reason = None
            item.override_approved_by = None

        return True, "Price updated successfully."

    def calculate_cart_summary(
        self,
        cart: List[CartItem],
        bill_discount: Decimal = Decimal("0.00"),
        tax_percent: Decimal = Decimal("0.00")
    ) -> Dict[str, Decimal]:
        """Calculates subtotal, discounts, taxes, and final grand total."""
        subtotal = sum((item.line_total for item in cart), Decimal("0.00"))
        subtotal = to_decimal(subtotal)

        discount = to_decimal(bill_discount)
        if discount > subtotal:
            discount = subtotal

        taxable_amount = subtotal - discount
        tax_amount = to_decimal((taxable_amount * tax_percent) / Decimal("100.00"))
        grand_total = to_decimal(taxable_amount + tax_amount)

        # Estimate COGS and Gross Profit for manager
        total_cogs = sum((to_decimal(item.quantity * item.cost_price) for item in cart), Decimal("0.00"))
        gross_profit = grand_total - total_cogs

        return {
            "subtotal": subtotal,
            "discount_amount": discount,
            "tax_amount": tax_amount,
            "grand_total": grand_total,
            "cogs": total_cogs,
            "gross_profit": gross_profit,
            "total_items": sum((item.quantity for item in cart), Decimal("0.00"))
        }

    def complete_checkout(
        self,
        cart: List[CartItem],
        customer_id: Optional[int],
        cashier_id: Optional[int],
        payment_method: str,
        tendered_cash: Decimal,
        bill_discount: Decimal = Decimal("0.00"),
        notes: str = ""
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Finalizes checkout:
        - Validates cart has items
        - Computes totals
        - Handles payment status (paid, partial, unpaid)
        - Computes change returned
        - Commits to SQLite database via sales_repo
        - Returns (success, message, invoice_number)
        """
        if not cart:
            return False, "Cart is empty.", None

        tax_rate_str = self.settings_repo.get_setting("tax_rate_percent", "0.0")
        try:
            tax_rate = Decimal(tax_rate_str)
        except Exception:
            tax_rate = Decimal("0.0")

        summary = self.calculate_cart_summary(cart, bill_discount, tax_rate)
        grand_total = summary["grand_total"]

        # Validate payments
        paid_amount = to_decimal(tendered_cash)
        change_due = Decimal("0.00")

        if payment_method == "Cash":
            if paid_amount < grand_total and not customer_id:
                return False, f"Cash received (Rs. {paid_amount}) is less than Total (Rs. {grand_total}). Select a registered customer for credit sales.", None
            if paid_amount >= grand_total:
                change_due = paid_amount - grand_total
                paid_amount = grand_total
                balance_amount = Decimal("0.00")
                payment_status = "paid"
            else:
                balance_amount = grand_total - paid_amount
                payment_status = "partial"
        elif payment_method == "Credit":
            if not customer_id:
                return False, "Walk-in customers cannot make pure credit purchases. Please select or create a registered customer.", None
            balance_amount = grand_total
            paid_amount = Decimal("0.00")
            payment_status = "unpaid"
        else:  # Card, Online, Split
            balance_amount = Decimal("0.00")
            paid_amount = grand_total
            payment_status = "paid"

        invoice_no = self.sales_repo.generate_next_invoice_number()

        sale = Sale(
            id=None,
            invoice_number=invoice_no,
            customer_id=customer_id,
            cashier_id=cashier_id,
            sale_date="",
            subtotal=summary["subtotal"],
            discount_amount=summary["discount_amount"],
            discount_percent=Decimal("0.00"),
            tax_amount=summary["tax_amount"],
            grand_total=grand_total,
            paid_amount=paid_amount,
            balance_amount=balance_amount,
            payment_status=payment_status,
            payment_method=payment_method,
            notes=notes,
            items=cart
        )

        try:
            self.sales_repo.record_sale(sale, tendered_cash=tendered_cash, change_due=change_due)
            return True, f"Sale completed successfully. Change: Rs. {change_due:,.2f}", invoice_no
        except Exception as e:
            return False, f"Checkout failed: {str(e)}", None
