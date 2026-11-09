"""
Product, Variant & Inventory Management Screen for Arooj POS
Allows shop owners to configure catalog templates, enter real opening stock,
manage fabric rolls (thaans), and adjust stock quantities.
"""

from decimal import Decimal
from typing import Optional
from app.config import format_currency, to_decimal, to_qty_decimal
from app.models.entities import FabricRoll

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QComboBox, QHeaderView, QMessageBox, QDialog,
        QDoubleSpinBox, QFormLayout
    )
    from PySide6.QtCore import Qt
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class StockSetupDialog(QDialog):
        """Allows owner to enter real purchase cost, selling price, and opening stock for a product."""
        def __init__(self, product, variant, parent=None):
            super().__init__(parent)
            self.product = product
            self.variant = variant
            self.setWindowTitle(f"Opening Stock & Pricing: {product.name}")
            self.setMinimumWidth(360)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            title = f"{self.product.name} - {self.variant.display_title() if self.variant else 'Standard'}"
            layout.addWidget(QLabel(f"<b>{title}</b>"))

            self.cost_spin = QDoubleSpinBox()
            self.cost_spin.setRange(0.0, 1000000.0)
            self.cost_spin.setValue(float(self.variant.cost_price if self.variant else self.product.base_cost_price))
            form.addRow("Purchase Cost (Rs.):", self.cost_spin)

            self.price_spin = QDoubleSpinBox()
            self.price_spin.setRange(0.0, 1000000.0)
            self.price_spin.setValue(float(self.variant.selling_price if self.variant else self.product.base_selling_price))
            form.addRow("Selling Price (Rs.):", self.price_spin)

            self.stock_spin = QDoubleSpinBox()
            self.stock_spin.setRange(0.0, 100000.0)
            self.stock_spin.setDecimals(2)
            self.stock_spin.setValue(float(self.variant.stock_quantity if self.variant else 0.0))
            form.addRow(f"Opening Stock ({self.product.unit_name or 'Units'}):", self.stock_spin)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            save = QPushButton("Save & Activate")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.accept)
            btn_box.addWidget(cancel)
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

    class ProductManagementScreen(QWidget):
        def __init__(self, catalog_repo, inventory_repo, user_id=1, parent=None):
            super().__init__(parent)
            self.catalog_repo = catalog_repo
            self.inventory_repo = inventory_repo
            self.user_id = user_id
            self.init_ui()
            self.load_products()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            top_box = QHBoxLayout()
            title = QLabel("Stock & Catalog Management (سٹاک اور کیٹلاگ)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            top_box.addWidget(title)
            top_box.addStretch()

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search item to update stock or price...")
            self.search_input.setFixedWidth(260)
            self.search_input.textChanged.connect(self.load_products)
            top_box.addWidget(self.search_input)

            layout.addLayout(top_box)

            # Table of Products and Variants
            self.table = QTableWidget()
            self.table.setColumnCount(8)
            self.table.setHorizontalHeaderLabels([
                "Code / SKU", "Category", "Product Name", "Variety / Size", "Unit", "Cost (Rs.)", "Sale Rate (Rs.)", "Stock On-Hand"
            ])
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.doubleClicked.connect(self.on_row_double_click)
            layout.addWidget(self.table)

            # Action button bar
            btn_box = QHBoxLayout()
            edit_btn = QPushButton("Set Stock & Pricing (F2)")
            edit_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 16px;")
            edit_btn.clicked.connect(self.on_edit_selected)

            add_roll_btn = QPushButton("Add Fabric Thaan / Roll (تھان داخل کریں)")
            add_roll_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 10px 16px;")
            add_roll_btn.clicked.connect(self.on_add_roll)

            btn_box.addWidget(edit_btn)
            btn_box.addWidget(add_roll_btn)
            btn_box.addStretch()
            layout.addLayout(btn_box)

        def load_products(self):
            search = self.search_input.text().strip()
            prods = self.catalog_repo.get_products(search_term=search if search else None)

            # Flatten variants
            self.row_map = []
            for p in prods:
                if p.variants:
                    for v in p.variants:
                        self.row_map.append((p, v))
                else:
                    self.row_map.append((p, None))

            self.table.setRowCount(len(self.row_map))
            for i, (p, v) in enumerate(self.row_map):
                sku = v.sku if v else p.code
                var_desc = v.display_title() if v else "Standard"
                cost = v.cost_price if v else p.base_cost_price
                price = v.selling_price if v else p.base_selling_price
                stock = v.stock_quantity if v else Decimal("0.000")

                self.table.setItem(i, 0, QTableWidgetItem(sku))
                self.table.setItem(i, 1, QTableWidgetItem(p.category_name or ""))
                self.table.setItem(i, 2, QTableWidgetItem(p.name))
                self.table.setItem(i, 3, QTableWidgetItem(var_desc))
                self.table.setItem(i, 4, QTableWidgetItem(p.unit_name or "Pcs"))
                self.table.setItem(i, 5, QTableWidgetItem(f"{cost:,.2f}"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{price:,.2f}"))
                self.table.setItem(i, 7, QTableWidgetItem(f"{stock:g}"))

        def on_edit_selected(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Item", "Please select a row to configure opening stock and prices.")
                return
            p, v = self.row_map[row]
            dlg = StockSetupDialog(p, v, self)
            if dlg.exec() == QDialog.Accepted:
                new_cost = to_decimal(dlg.cost_spin.value())
                new_price = to_decimal(dlg.price_spin.value())
                new_stock = to_qty_decimal(dlg.stock_spin.value())

                if v:
                    self.catalog_repo.update_variant_pricing_stock(v.id, new_cost, new_price, new_stock)
                    self.inventory_repo.set_opening_stock(v.id, new_stock, new_cost, self.user_id)
                self.load_products()

        def on_row_double_click(self, index):
            self.on_edit_selected()

        def on_add_roll(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Fabric", "Please select a fabric product row to register a new thaan / roll.")
                return
            p, v = self.row_map[row]
            if not p.is_fabric:
                QMessageBox.warning(self, "Not a Fabric", f"'{p.name}' is sold as piece/set, not fabric by meter/yard.")
                return

            import datetime
            roll_num = f"TH-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
            roll = FabricRoll(
                id=None,
                product_id=p.id,
                variant_id=v.id if v else None,
                roll_number=roll_num,
                initial_length=Decimal("40.000"),  # standard 40 meters
                current_length=Decimal("40.000"),
                unit_name=p.unit_name or "Meter",
                cost_per_unit=v.cost_price if v else Decimal("0.00"),
                notes="New thaan arrived from mill"
            )
            self.inventory_repo.add_fabric_roll(roll)
            QMessageBox.information(self, "Fabric Roll Registered", f"New Thaan #{roll_num} registered with 40 {p.unit_name}!")
            self.load_products()
else:
    class ProductManagementScreen:
        pass
