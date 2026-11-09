"""
Visual Product Cards & Variant Selector for Arooj POS Billing Screen
"""

from decimal import Decimal
from typing import List, Optional, Callable
from app.models.entities import Product, ProductVariant
from app.config import format_currency, to_qty_decimal

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
        QScrollArea, QFrame, QDialog, QRadioButton, QButtonGroup, QDoubleSpinBox,
        QMessageBox
    )
    from PySide6.QtCore import Qt, Signal
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object
    Signal = lambda *args: None

if PYSIDE_AVAILABLE:
    class VariantSelectionDialog(QDialog):
        """Compact modal allowing cashier to select size/color/design variant and fabric meters."""

        def __init__(self, product: Product, parent=None):
            super().__init__(parent)
            self.product = product
            self.selected_variant: Optional[ProductVariant] = None
            self.quantity = Decimal("1.000")
            self.setWindowTitle(f"Select Variant: {product.name}")
            self.setMinimumWidth(380)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(12)

            title_lbl = QLabel(f"<b>{self.product.name}</b>")
            title_lbl.setStyleSheet("font-size: 15px; color: #064e3b;")
            layout.addWidget(title_lbl)

            layout.addWidget(QLabel("Available Varieties / Sizes / Colors:"))

            self.btn_group = QButtonGroup(self)
            self.variant_radios = []

            for idx, v in enumerate(self.product.variants):
                price_str = f"Rs. {v.selling_price:,.0f}" if v.selling_price > 0 else "Unset"
                stock_str = f"Stock: {v.stock_quantity:g}"
                desc = f"{v.display_title()}  |  {price_str}  ({stock_str})"

                rb = QRadioButton(desc)
                if idx == 0:
                    rb.setChecked(True)
                self.btn_group.addButton(rb, idx)
                self.variant_radios.append((rb, v))
                layout.addWidget(rb)

            # If fabric sold by meter / yard, show decimal quantity selector
            if self.product.is_fabric:
                layout.addWidget(QLabel(f"Length in {self.product.unit_name or 'Meters'}:"))
                self.qty_spin = QDoubleSpinBox()
                self.qty_spin.setRange(0.1, 1000.0)
                self.qty_spin.setDecimals(2)
                self.qty_spin.setSingleStep(0.5)
                self.qty_spin.setValue(1.0)
                layout.addWidget(self.qty_spin)
            else:
                self.qty_spin = None

            # Buttons
            btn_box = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            ok_btn = QPushButton("Add to Cart")
            ok_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px;")
            ok_btn.clicked.connect(self.on_confirm)

            btn_box.addWidget(cancel_btn)
            btn_box.addWidget(ok_btn)
            layout.addLayout(btn_box)

        def on_confirm(self):
            checked_id = self.btn_group.checkedId()
            if checked_id >= 0 and checked_id < len(self.variant_radios):
                self.selected_variant = self.variant_radios[checked_id][1]
            if self.qty_spin:
                self.quantity = to_qty_decimal(self.qty_spin.value())
            self.accept()

    class ProductCard(QFrame):
        """Visual product card for rapid one-touch billing."""
        clicked = Signal(object, object, Decimal)  # product, variant, quantity

        def __init__(self, product: Product, parent=None):
            super().__init__(parent)
            self.product = product
            self.setObjectName("productCard")
            self.setProperty("class", "productCard")
            self.setCursor(Qt.PointingHandCursor)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(6)

            # Category Tag & Code
            tag_box = QHBoxLayout()
            cat_lbl = QLabel(self.product.category_name or "Item")
            cat_lbl.setStyleSheet("font-size: 10px; color: #047857; font-weight: bold; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;")
            code_lbl = QLabel(self.product.code)
            code_lbl.setStyleSheet("font-size: 10px; color: #64748b;")
            tag_box.addWidget(cat_lbl)
            tag_box.addStretch()
            tag_box.addWidget(code_lbl)
            layout.addLayout(tag_box)

            # Product Name
            name_lbl = QLabel(self.product.name)
            name_lbl.setWordWrap(True)
            name_lbl.setStyleSheet("font-weight: 700; font-size: 13px; color: #0f172a;")
            layout.addWidget(name_lbl)

            # Urdu name if available
            if self.product.name_urdu:
                urdu_lbl = QLabel(self.product.name_urdu)
                urdu_lbl.setStyleSheet("font-size: 12px; color: #059669; font-weight: 600;")
                layout.addWidget(urdu_lbl)

            layout.addStretch()

            # Price & Variants info
            bottom_box = QHBoxLayout()
            price_val = self.product.base_selling_price
            if self.product.variants and self.product.variants[0].selling_price > 0:
                price_val = self.product.variants[0].selling_price

            price_str = format_currency(price_val) if price_val > 0 else "Rs. Unset"
            price_lbl = QLabel(price_str)
            price_lbl.setStyleSheet("font-size: 14px; font-weight: 800; color: #047857;")

            var_count = len(self.product.variants)
            badge_text = f"{var_count} Types" if var_count > 1 else (self.product.unit_name or "Pcs")
            var_lbl = QLabel(badge_text)
            var_lbl.setStyleSheet("font-size: 11px; color: #475569; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;")

            bottom_box.addWidget(price_lbl)
            bottom_box.addStretch()
            bottom_box.addWidget(var_lbl)
            layout.addLayout(bottom_box)

        def mousePressEvent(self, event):
            if event.button() == Qt.LeftButton:
                if len(self.product.variants) > 1 or self.product.is_fabric:
                    dialog = VariantSelectionDialog(self.product, self.window())
                    if dialog.exec() == QDialog.Accepted:
                        self.clicked.emit(self.product, dialog.selected_variant, dialog.quantity)
                else:
                    var = self.product.variants[0] if self.product.variants else None
                    self.clicked.emit(self.product, var, Decimal("1.000"))
            super().mousePressEvent(event)

    class ProductGridWidget(QScrollArea):
        product_selected = Signal(object, object, Decimal)

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWidgetResizable(True)
            self.container = QWidget()
            self.grid_layout = QGridLayout(self.container)
            self.grid_layout.setContentsMargins(12, 12, 12, 12)
            self.grid_layout.setSpacing(12)
            self.setWidget(self.container)

        def set_products(self, products: List[Product]):
            # Clear existing cards
            while self.grid_layout.count():
                item = self.grid_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            if not products:
                empty_lbl = QLabel("No products found in this category.")
                empty_lbl.setStyleSheet("font-size: 14px; color: #64748b; padding: 40px;")
                empty_lbl.setAlignment(Qt.AlignCenter)
                self.grid_layout.addWidget(empty_lbl, 0, 0)
                return

            columns = 3
            for idx, prod in enumerate(products):
                card = ProductCard(prod)
                card.clicked.connect(self.product_selected.emit)
                row = idx // columns
                col = idx % columns
                self.grid_layout.addWidget(card, row, col)
else:
    class ProductGridWidget:
        pass
