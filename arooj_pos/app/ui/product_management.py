"""
Product, Variant & Inventory Management Screen for Arooj POS
Supports:
- Add New Product with English & Urdu names, auto-SKU, auto-barcode, category/subcategory
- Edit Existing Product safely preserving historical transaction data
- Variant Manager (Size, Colour, Brand, Design, Fabric Type, individual prices and stocks)
- Printable Barcode Labels with preview and printer output
- Manual opening stock entry and variant pricing
- Fabric rolls (thaans) tracking
- Bulk Excel & CSV product import with preview, validation, and mode selection
- Export catalog to CSV/Excel
- Safe deactivation (never deleting historical records)
"""

from decimal import Decimal
from typing import Optional, List
from pathlib import Path

from app.config import format_currency, to_decimal, to_qty_decimal
from app.models.entities import FabricRoll, Product, ProductVariant
from app.services.import_export_service import ImportExportService
from app.ui.barcode_label_dialog import BarcodeLabelDialog

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QComboBox, QHeaderView, QMessageBox, QDialog,
        QDoubleSpinBox, QSpinBox, QFormLayout, QFileDialog, QRadioButton, QButtonGroup,
        QTextEdit, QFrame, QCheckBox, QTabWidget, QGroupBox, QSplitter
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor
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
            self.setMinimumWidth(400)
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
            self.stock_spin.setDecimals(3 if self.product.is_fabric else 0)
            self.stock_spin.setValue(float(self.variant.stock_quantity if self.variant else 0.0))
            form.addRow(f"Opening Stock ({self.product.unit_name or 'Units'}):", self.stock_spin)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            save = QPushButton("Save & Update")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.accept)
            btn_box.addWidget(cancel)
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

    class ProductFormDialog(QDialog):
        """Comprehensive dialog for adding or editing a product."""
        def __init__(self, catalog_repo, product=None, user_id=1, parent=None):
            super().__init__(parent)
            self.catalog_repo = catalog_repo
            self.product = product
            self.user_id = user_id
            self.is_edit = product is not None
            self.setWindowTitle("Edit Product (پراڈکٹ کی تفصیلات)" if self.is_edit else "Add New Product (نیا پراڈکٹ شامل کریں)")
            self.resize(580, 560)
            self.init_ui()
            if self.is_edit:
                self.populate_data()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(10)

            form = QFormLayout()

            # Name English
            self.name_input = QLineEdit()
            self.name_input.setPlaceholderText("e.g. Cotton King Bedsheet Set, Lawn Digital Printed")
            form.addRow("Product Name (English)*:", self.name_input)

            # Name Urdu
            self.name_urdu_input = QLineEdit()
            self.name_urdu_input.setPlaceholderText("مثال: کاٹن کنگ بیڈ شیٹ سیٹ، لان پرنٹڈ")
            form.addRow("Product Name (Urdu):", self.name_urdu_input)

            # Category & Subcategory
            cat_row = QHBoxLayout()
            self.cat_combo = QComboBox()
            self.subcat_combo = QComboBox()
            self.categories = self.catalog_repo.get_categories(only_active=False)
            for c in self.categories:
                self.cat_combo.addItem(f"{c.name} ({c.name_urdu or ''})", c.id)
            self.cat_combo.currentIndexChanged.connect(self.on_category_changed)
            cat_row.addWidget(self.cat_combo)
            cat_row.addWidget(QLabel("Subcategory:"))
            cat_row.addWidget(self.subcat_combo)
            form.addRow("Category*:", cat_row)
            self.on_category_changed()

            # SKU and Barcode with Auto-Generate buttons
            sku_row = QHBoxLayout()
            self.sku_input = QLineEdit()
            self.sku_input.setPlaceholderText("Unique SKU / Code")
            gen_sku_btn = QPushButton("⚡ Auto SKU")
            gen_sku_btn.clicked.connect(self.on_auto_sku)
            sku_row.addWidget(self.sku_input)
            sku_row.addWidget(gen_sku_btn)
            form.addRow("SKU / Item Code*:", sku_row)

            barcode_row = QHBoxLayout()
            self.barcode_input = QLineEdit()
            self.barcode_input.setPlaceholderText("EAN-13 or Code-128 Barcode")
            gen_barcode_btn = QPushButton("⚡ Auto Barcode")
            gen_barcode_btn.clicked.connect(self.on_auto_barcode)
            barcode_row.addWidget(self.barcode_input)
            barcode_row.addWidget(gen_barcode_btn)
            form.addRow("Barcode:", barcode_row)

            # Unit
            self.unit_combo = QComboBox()
            self.units = self.catalog_repo.get_units()
            for u in self.units:
                self.unit_combo.addItem(f"{u.name} ({u.symbol})", u.id)
            form.addRow("Selling Unit*:", self.unit_combo)

            # Product Type
            type_row = QHBoxLayout()
            self.rb_standard = QRadioButton("Standard Product (Piece/Set)")
            self.rb_variants = QRadioButton("Has Size/Color Variants")
            self.rb_fabric = QRadioButton("Fabric (Meter / Gaz)")
            self.rb_standard.setChecked(True)

            self.type_group = QButtonGroup(self)
            self.type_group.addButton(self.rb_standard, 1)
            self.type_group.addButton(self.rb_variants, 2)
            self.type_group.addButton(self.rb_fabric, 3)

            type_row.addWidget(self.rb_standard)
            type_row.addWidget(self.rb_variants)
            type_row.addWidget(self.rb_fabric)
            form.addRow("Product Nature:", type_row)

            # Pricing & Stock
            price_row = QHBoxLayout()
            self.cost_spin = QDoubleSpinBox()
            self.cost_spin.setRange(0.0, 1000000.0)
            self.cost_spin.setValue(0.0)

            self.price_spin = QDoubleSpinBox()
            self.price_spin.setRange(0.0, 1000000.0)
            self.price_spin.setValue(0.0)

            price_row.addWidget(QLabel("Cost (Rs.):"))
            price_row.addWidget(self.cost_spin)
            price_row.addWidget(QLabel("Sale Price (Rs.)*:"))
            price_row.addWidget(self.price_spin)
            form.addRow("Pricing:", price_row)

            stock_row = QHBoxLayout()
            self.stock_spin = QDoubleSpinBox()
            self.stock_spin.setRange(0.0, 100000.0)
            self.stock_spin.setDecimals(3)
            self.stock_spin.setValue(0.0)

            self.alert_spin = QDoubleSpinBox()
            self.alert_spin.setRange(0.0, 1000.0)
            self.alert_spin.setDecimals(1)
            self.alert_spin.setValue(5.0)

            stock_row.addWidget(QLabel("Opening Stock:"))
            stock_row.addWidget(self.stock_spin)
            stock_row.addWidget(QLabel("Min Alert Qty:"))
            stock_row.addWidget(self.alert_spin)
            form.addRow("Stock Control:", stock_row)

            # Description
            self.desc_input = QLineEdit()
            self.desc_input.setPlaceholderText("Brand name, cloth material, thaan length, etc.")
            form.addRow("Description / Brand:", self.desc_input)

            # Active Checkbox
            self.chk_active = QCheckBox("Product is Active for Sales and Stock (فعال)")
            self.chk_active.setChecked(True)
            form.addRow("", self.chk_active)

            layout.addLayout(form)

            # Bottom buttons
            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            save = QPushButton("Save Product (محفوظ کریں)")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 8px 18px;")
            save.clicked.connect(self.on_save)

            btn_box.addWidget(cancel)
            btn_box.addStretch()
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

            if not self.is_edit:
                self.on_auto_sku()
                self.on_auto_barcode()

        def on_category_changed(self):
            cat_id = self.cat_combo.currentData()
            self.subcat_combo.clear()
            self.subcat_combo.addItem("None", None)
            if cat_id:
                subcats = self.catalog_repo.get_subcategories(cat_id, only_active=False)
                for sc in subcats:
                    self.subcat_combo.addItem(f"{sc.name}", sc.id)

        def on_auto_sku(self):
            sku = self.catalog_repo.generate_unique_sku("PRD")
            self.sku_input.setText(sku)

        def on_auto_barcode(self):
            barcode = self.catalog_repo.generate_unique_barcode("200")
            self.barcode_input.setText(barcode)

        def populate_data(self):
            p = self.product
            self.name_input.setText(p.name)
            self.name_urdu_input.setText(p.name_urdu or "")

            idx = self.cat_combo.findData(p.category_id)
            if idx >= 0:
                self.cat_combo.setCurrentIndex(idx)
            self.on_category_changed()
            if p.subcategory_id:
                sc_idx = self.subcat_combo.findData(p.subcategory_id)
                if sc_idx >= 0:
                    self.subcat_combo.setCurrentIndex(sc_idx)

            self.sku_input.setText(p.code)
            self.barcode_input.setText(p.barcode or "")

            u_idx = self.unit_combo.findData(p.unit_id)
            if u_idx >= 0:
                self.unit_combo.setCurrentIndex(u_idx)

            if p.is_template:
                self.rb_variants.setChecked(True)
            elif p.is_fabric:
                self.rb_fabric.setChecked(True)
            else:
                self.rb_standard.setChecked(True)

            self.cost_spin.setValue(float(p.base_cost_price))
            self.price_spin.setValue(float(p.base_selling_price))

            # If standard, get stock from default variant
            stock = 0.0
            if p.variants:
                stock = float(p.variants[0].stock_quantity)
            self.stock_spin.setValue(stock)
            self.alert_spin.setValue(float(p.min_stock_alert))
            self.desc_input.setText(p.description or "")
            self.chk_active.setChecked(p.is_active)

        def on_save(self):
            name = self.name_input.text().strip()
            if not name:
                QMessageBox.warning(self, "Validation Error", "Product Name (English) is required.")
                return

            sku = self.sku_input.text().strip()
            if not sku:
                QMessageBox.warning(self, "Validation Error", "SKU / Item Code is required.")
                return

            barcode = self.barcode_input.text().strip() or None
            # Check unique SKU
            exclude_p = self.product.id if self.is_edit else None
            if self.catalog_repo.sku_exists(sku, exclude_product_id=exclude_p):
                QMessageBox.warning(self, "Duplicate SKU", f"SKU '{sku}' already exists in the system. Please use a unique SKU.")
                return

            # Check unique Barcode if provided
            if barcode and self.catalog_repo.barcode_exists(barcode, exclude_product_id=exclude_p):
                QMessageBox.warning(self, "Duplicate Barcode", f"Barcode '{barcode}' is already assigned to another item.")
                return

            cat_id = self.cat_combo.currentData()
            subcat_id = self.subcat_combo.currentData()
            unit_id = self.unit_combo.currentData()
            name_urdu = self.name_urdu_input.text().strip() or None
            cost = to_decimal(self.cost_spin.value())
            price = to_decimal(self.price_spin.value())
            stock = to_qty_decimal(self.stock_spin.value())
            min_alert = to_qty_decimal(self.alert_spin.value())
            desc = self.desc_input.text().strip() or None
            is_active = self.chk_active.isChecked()
            is_template = self.rb_variants.isChecked()
            is_fabric = self.rb_fabric.isChecked()

            if self.is_edit:
                self.catalog_repo.update_product(
                    product_id=self.product.id,
                    category_id=cat_id,
                    subcategory_id=subcat_id,
                    code=sku,
                    barcode=barcode,
                    name=name,
                    name_urdu=name_urdu,
                    unit_id=unit_id,
                    is_fabric=is_fabric,
                    min_stock_alert=min_alert,
                    base_cost_price=cost,
                    base_selling_price=price,
                    description=desc,
                    is_active=is_active,
                    stock_quantity=stock if not self.product.is_template else None
                )
            else:
                self.catalog_repo.create_product(
                    category_id=cat_id,
                    subcategory_id=subcat_id,
                    code=sku,
                    barcode=barcode,
                    name=name,
                    name_urdu=name_urdu,
                    unit_id=unit_id,
                    is_template=is_template,
                    is_fabric=is_fabric,
                    min_stock_alert=min_alert,
                    base_cost_price=cost,
                    base_selling_price=price,
                    description=desc,
                    opening_stock=stock,
                    is_active=is_active,
                    user_id=self.user_id
                )

            self.accept()

    class VariantFormDialog(QDialog):
        """Add or Edit individual product variant (Size, Color, Design, Price, Stock)."""
        def __init__(self, catalog_repo, product, variant=None, user_id=1, parent=None):
            super().__init__(parent)
            self.catalog_repo = catalog_repo
            self.product = product
            self.variant = variant
            self.user_id = user_id
            self.is_edit = variant is not None
            self.setWindowTitle(f"{'Edit' if self.is_edit else 'Add'} Variant for {product.name}")
            self.resize(460, 480)
            self.init_ui()
            if self.is_edit:
                self.populate_data()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            # SKU and Barcode
            sku_row = QHBoxLayout()
            self.sku_input = QLineEdit()
            self.sku_input.setPlaceholderText("e.g. BED-KING-MAROON")
            auto_btn = QPushButton("Auto")
            auto_btn.clicked.connect(self.on_auto_sku)
            sku_row.addWidget(self.sku_input)
            sku_row.addWidget(auto_btn)
            form.addRow("Variant SKU*:", sku_row)

            bar_row = QHBoxLayout()
            self.barcode_input = QLineEdit()
            self.barcode_input.setPlaceholderText("Barcode sticker code")
            auto_bar_btn = QPushButton("Auto")
            auto_bar_btn.clicked.connect(self.on_auto_barcode)
            bar_row.addWidget(self.barcode_input)
            bar_row.addWidget(auto_bar_btn)
            form.addRow("Variant Barcode:", bar_row)

            self.size_input = QLineEdit()
            self.size_input.setPlaceholderText("e.g. King, Queen, Single, 7x8 ft")
            form.addRow("Size / Dimension:", self.size_input)

            self.color_input = QLineEdit()
            self.color_input.setPlaceholderText("e.g. Maroon, Navy Blue, Grey, Off-White")
            form.addRow("Colour / Shade:", self.color_input)

            self.design_input = QLineEdit()
            self.design_input.setPlaceholderText("e.g. Floral, Geometric, Plain, Embroidery")
            form.addRow("Design / Pattern:", self.design_input)

            self.fabric_input = QLineEdit()
            self.fabric_input.setPlaceholderText("e.g. 100% Pure Cotton, Velvet, Lawn, Jacquard")
            form.addRow("Fabric Type:", self.fabric_input)

            self.cost_spin = QDoubleSpinBox()
            self.cost_spin.setRange(0.0, 1000000.0)
            self.cost_spin.setValue(float(self.product.base_cost_price))
            form.addRow("Cost Price (Rs.):", self.cost_spin)

            self.price_spin = QDoubleSpinBox()
            self.price_spin.setRange(0.0, 1000000.0)
            self.price_spin.setValue(float(self.product.base_selling_price))
            form.addRow("Selling Price (Rs.)*:", self.price_spin)

            self.stock_spin = QDoubleSpinBox()
            self.stock_spin.setRange(0.0, 100000.0)
            self.stock_spin.setDecimals(3 if self.product.is_fabric else 0)
            self.stock_spin.setValue(0.0)
            form.addRow("Stock Quantity:", self.stock_spin)

            self.chk_active = QCheckBox("Variant is Active for Billing")
            self.chk_active.setChecked(True)
            form.addRow("", self.chk_active)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)
            save = QPushButton("Save Variant")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.on_save)
            btn_box.addWidget(cancel)
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

            if not self.is_edit:
                self.on_auto_sku()
                self.on_auto_barcode()

        def on_auto_sku(self):
            prefix = self.product.code
            v_sku = self.catalog_repo.generate_unique_sku(prefix)
            self.sku_input.setText(v_sku)

        def on_auto_barcode(self):
            barcode = self.catalog_repo.generate_unique_barcode("200")
            self.barcode_input.setText(barcode)

        def populate_data(self):
            v = self.variant
            self.sku_input.setText(v.sku)
            self.barcode_input.setText(v.barcode or "")
            self.size_input.setText(v.size or "")
            self.color_input.setText(v.color or "")
            self.design_input.setText(v.design or "")
            self.fabric_input.setText(v.fabric_type or "")
            self.cost_spin.setValue(float(v.cost_price))
            self.price_spin.setValue(float(v.selling_price))
            self.stock_spin.setValue(float(v.stock_quantity))
            self.chk_active.setChecked(v.is_active)

        def on_save(self):
            sku = self.sku_input.text().strip()
            if not sku:
                QMessageBox.warning(self, "Validation", "Variant SKU is required.")
                return

            barcode = self.barcode_input.text().strip() or None
            exclude_v = self.variant.id if self.is_edit else None

            if self.catalog_repo.sku_exists(sku, exclude_variant_id=exclude_v):
                QMessageBox.warning(self, "Duplicate SKU", f"SKU '{sku}' already exists.")
                return

            if barcode and self.catalog_repo.barcode_exists(barcode, exclude_variant_id=exclude_v):
                QMessageBox.warning(self, "Duplicate Barcode", f"Barcode '{barcode}' already exists.")
                return

            cost = to_decimal(self.cost_spin.value())
            price = to_decimal(self.price_spin.value())
            stock = to_qty_decimal(self.stock_spin.value())
            is_active = self.chk_active.isChecked()

            if self.is_edit:
                self.catalog_repo.update_variant(
                    variant_id=self.variant.id,
                    sku=sku,
                    barcode=barcode,
                    size=self.size_input.text().strip() or None,
                    color=self.color_input.text().strip() or None,
                    design=self.design_input.text().strip() or None,
                    fabric_type=self.fabric_input.text().strip() or None,
                    cost_price=cost,
                    selling_price=price,
                    stock_quantity=stock,
                    is_active=is_active
                )
            else:
                self.catalog_repo.create_variant(
                    product_id=self.product.id,
                    sku=sku,
                    barcode=barcode,
                    size=self.size_input.text().strip() or None,
                    color=self.color_input.text().strip() or None,
                    design=self.design_input.text().strip() or None,
                    fabric_type=self.fabric_input.text().strip() or None,
                    cost_price=cost,
                    selling_price=price,
                    stock_quantity=stock,
                    is_active=is_active,
                    user_id=self.user_id
                )

            self.accept()

    class FabricRollDialog(QDialog):
        """Allows user to enter specific details when adding a fabric thaan / roll."""
        def __init__(self, product, variant=None, parent=None):
            super().__init__(parent)
            self.product = product
            self.variant = variant
            self.setWindowTitle(f"Add Fabric Thaan / Roll: {product.name}")
            self.resize(440, 320)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            form = QFormLayout()

            import datetime
            suggested_num = f"TH-{datetime.datetime.now().strftime('%y%m%d%H%M')}"
            self.num_input = QLineEdit(suggested_num)
            form.addRow("Roll / Thaan #*:", self.num_input)

            self.length_spin = QDoubleSpinBox()
            self.length_spin.setRange(0.1, 10000.0)
            self.length_spin.setDecimals(3)
            self.length_spin.setValue(40.0)
            unit_lbl = self.product.unit_name or "Meter"
            form.addRow(f"Roll Length ({unit_lbl})*:", self.length_spin)

            self.cost_spin = QDoubleSpinBox()
            self.cost_spin.setRange(0.0, 100000.0)
            default_cost = float(self.variant.cost_price if self.variant else self.product.base_cost_price)
            self.cost_spin.setValue(default_cost)
            form.addRow("Cost per Unit (Rs.):", self.cost_spin)

            self.notes_input = QLineEdit()
            self.notes_input.setPlaceholderText("Mill name, lot number, shade, quality notes...")
            form.addRow("Notes / Mill:", self.notes_input)

            layout.addLayout(form)

            btn_box = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)
            save_btn = QPushButton("Save Thaan / Roll")
            save_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save_btn.clicked.connect(self.accept)

            btn_box.addWidget(cancel_btn)
            btn_box.addStretch()
            btn_box.addWidget(save_btn)
            layout.addLayout(btn_box)

    class VariantManagerDialog(QDialog):
        """Manage all variants under a parent product."""
        def __init__(self, catalog_repo, product, user_id=1, parent=None):
            super().__init__(parent)
            self.catalog_repo = catalog_repo
            self.product = product
            self.user_id = user_id
            self.setWindowTitle(f"Manage Variants: {product.name}")
            self.resize(760, 480)
            self.init_ui()
            self.load_variants()

        def init_ui(self):
            layout = QVBoxLayout(self)

            top_info = QLabel(f"<b>Parent Product:</b> {self.product.name} (Code: {self.product.code})")
            top_info.setStyleSheet("font-size: 13px; color: #064e3b;")
            layout.addWidget(top_info)

            self.table = QTableWidget()
            self.table.setColumnCount(8)
            self.table.setHorizontalHeaderLabels([
                "SKU", "Barcode", "Size / Dimension", "Color / Design", "Cost Price", "Sale Price", "Stock", "Status"
            ])
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            layout.addWidget(self.table)

            btn_box = QHBoxLayout()
            add_btn = QPushButton("➕ Add New Variant")
            add_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 6px 14px;")
            add_btn.clicked.connect(self.on_add_variant)

            edit_btn = QPushButton("✏️ Edit Variant")
            edit_btn.clicked.connect(self.on_edit_variant)

            deact_btn = QPushButton("🚫 Deactivate Variant")
            deact_btn.clicked.connect(self.on_deactivate_variant)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)

            btn_box.addWidget(add_btn)
            btn_box.addWidget(edit_btn)
            btn_box.addWidget(deact_btn)
            btn_box.addStretch()
            btn_box.addWidget(close_btn)
            layout.addLayout(btn_box)

        def load_variants(self):
            self.variants = self.catalog_repo.get_variants_for_product(self.product.id, only_active=False)
            self.table.setRowCount(len(self.variants))
            for i, v in enumerate(self.variants):
                self.table.setItem(i, 0, QTableWidgetItem(v.sku))
                self.table.setItem(i, 1, QTableWidgetItem(v.barcode or "-"))
                self.table.setItem(i, 2, QTableWidgetItem(v.size or "-"))
                self.table.setItem(i, 3, QTableWidgetItem(f"{v.color or ''} {v.design or ''}".strip() or "-"))
                self.table.setItem(i, 4, QTableWidgetItem(f"{v.cost_price:,.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(f"{v.selling_price:,.2f}"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{v.stock_quantity:g}"))
                status_item = QTableWidgetItem("Active" if v.is_active else "Inactive")
                status_item.setForeground(QColor("#059669" if v.is_active else "#dc2626"))
                self.table.setItem(i, 7, status_item)

        def on_add_variant(self):
            dlg = VariantFormDialog(self.catalog_repo, self.product, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_variants()

        def on_edit_variant(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.variants):
                QMessageBox.information(self, "Select Variant", "Please select a variant to edit.")
                return
            v = self.variants[row]
            dlg = VariantFormDialog(self.catalog_repo, self.product, variant=v, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_variants()

        def on_deactivate_variant(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.variants):
                QMessageBox.information(self, "Select Variant", "Please select a variant to deactivate.")
                return
            v = self.variants[row]
            self.catalog_repo.deactivate_variant(v.id)
            self.load_variants()

    class BulkImportDialog(QDialog):
        """Allows bulk importing hundreds/thousands of products from Excel or CSV files."""
        def __init__(self, conn, user_id=1, parent=None):
            super().__init__(parent)
            self.import_service = ImportExportService(conn)
            self.user_id = user_id
            self.selected_file_path = ""
            self.validation_summary = None

            self.setWindowTitle("Bulk Product Catalog Import (ایکسل / سی ایس وی امپورٹ)")
            self.resize(760, 560)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(12)

            # Top instructions & templates bar
            top_bar = QHBoxLayout()
            info_label = QLabel("Import products, varieties, prices, and stock in one operation.")
            info_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #064e3b;")

            template_btn = QPushButton("Download Blank Template")
            template_btn.clicked.connect(self.on_download_template)

            sample_btn = QPushButton("Download Sample File")
            sample_btn.clicked.connect(self.on_download_sample)

            top_bar.addWidget(info_label)
            top_bar.addStretch()
            top_bar.addWidget(template_btn)
            top_bar.addWidget(sample_btn)
            layout.addLayout(top_bar)

            # File selection box
            file_frame = QFrame()
            file_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px;")
            file_layout = QHBoxLayout(file_frame)

            self.file_path_label = QLabel("No file selected (.csv or .xlsx)")
            self.file_path_label.setStyleSheet("color: #64748b; font-weight: bold;")
            browse_btn = QPushButton("Browse Excel / CSV File...")
            browse_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 6px 14px;")
            browse_btn.clicked.connect(self.on_browse_file)

            file_layout.addWidget(self.file_path_label, stretch=1)
            file_layout.addWidget(browse_btn)
            layout.addWidget(file_frame)

            # Conflict Handling Mode
            mode_box = QHBoxLayout()
            mode_box.addWidget(QLabel("<b>Conflict Policy:</b>"))

            self.btn_group = QButtonGroup(self)
            self.rb_update = QRadioButton("Update matching existing products (اپ ڈیٹ کریں)")
            self.rb_skip = QRadioButton("Skip existing products (موجودہ کو چھوڑیں)")
            self.rb_new_only = QRadioButton("Add new only - error if exists (صرف نئے شامل کریں)")
            self.rb_skip.setChecked(True)

            self.btn_group.addButton(self.rb_skip, 1)
            self.btn_group.addButton(self.rb_update, 2)
            self.btn_group.addButton(self.rb_new_only, 3)

            mode_box.addWidget(self.rb_skip)
            mode_box.addWidget(self.rb_update)
            mode_box.addWidget(self.rb_new_only)
            mode_box.addStretch()
            layout.addLayout(mode_box)

            # Preview Table
            self.preview_table = QTableWidget()
            self.preview_table.setColumnCount(7)
            self.preview_table.setHorizontalHeaderLabels([
                "Row", "Category", "Product Name", "SKU", "Unit", "Cost Rate", "Sale Rate"
            ])
            self.preview_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
            layout.addWidget(self.preview_table)

            # Validation Status Output
            self.status_box = QLabel("Select an Excel or CSV file to preview and validate records.")
            self.status_box.setStyleSheet("color: #475569; font-weight: bold;")
            layout.addWidget(self.status_box)

            # Bottom Action Bar
            btn_box = QHBoxLayout()
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(self.reject)

            self.commit_btn = QPushButton("Import Verified Records into POS (امپورٹ کریں)")
            self.commit_btn.setEnabled(False)
            self.commit_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; font-size: 13px; padding: 10px 20px;")
            self.commit_btn.clicked.connect(self.on_commit_import)

            btn_box.addWidget(cancel_btn)
            btn_box.addStretch()
            btn_box.addWidget(self.commit_btn)
            layout.addLayout(btn_box)

        def on_download_template(self):
            dest, _ = QFileDialog.getSaveFileName(self, "Save Blank Template", "Arooj_POS_Import_Template.csv", "CSV (*.csv)")
            if dest:
                self.import_service.generate_template_csv(dest)
                QMessageBox.information(self, "Template Saved", f"Blank template saved successfully to:\n{dest}")

        def on_download_sample(self):
            dest, _ = QFileDialog.getSaveFileName(self, "Save Sample Catalog", "Arooj_POS_Sample_Catalog.csv", "CSV (*.csv)")
            if dest:
                self.import_service.generate_sample_csv(dest)
                QMessageBox.information(self, "Sample Saved", f"Sample catalog file saved successfully to:\n{dest}")

        def get_selected_mode(self) -> str:
            val = self.btn_group.checkedId()
            if val == 2:
                return "update"
            elif val == 3:
                return "add_only"
            return "skip"

        def on_browse_file(self):
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel or CSV File", "", "Spreadsheets (*.csv *.xlsx *.xls)")
            if not file_path:
                return

            self.selected_file_path = file_path
            self.file_path_label.setText(Path(file_path).name)

            try:
                mode = self.get_selected_mode()
                res = self.import_service.validate_and_import(file_path=file_path, mode=mode, commit=False, user_id=self.user_id)
                self.validation_summary = res

                records = res["valid_records"]
                self.preview_table.setRowCount(min(len(records), 100))
                for i, r in enumerate(records[:100]):
                    self.preview_table.setItem(i, 0, QTableWidgetItem(str(r["row_num"])))
                    self.preview_table.setItem(i, 1, QTableWidgetItem(r["category"]))
                    self.preview_table.setItem(i, 2, QTableWidgetItem(r["product_name"]))
                    self.preview_table.setItem(i, 3, QTableWidgetItem(r["sku"]))
                    self.preview_table.setItem(i, 4, QTableWidgetItem(r["unit"]))
                    self.preview_table.setItem(i, 5, QTableWidgetItem(str(r["cost_price"])))
                    self.preview_table.setItem(i, 6, QTableWidgetItem(str(r["selling_price"])))

                err_count = len(res["errors"])
                if err_count > 0:
                    self.status_box.setText(f"⚠️ Validation Warnings: {err_count} issues found. {len(records)} valid rows ready to import.")
                    self.status_box.setStyleSheet("color: #b45309; font-size: 12px; font-weight: bold;")
                    self.commit_btn.setEnabled(len(records) > 0)
                else:
                    self.status_box.setText(f"✅ Success: All {len(records)} product records are valid and ready to import!")
                    self.status_box.setStyleSheet("color: #059669; font-size: 12px; font-weight: bold;")
                    self.commit_btn.setEnabled(True)

            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Could not read file:\n{str(e)}")

        def on_commit_import(self):
            mode = self.get_selected_mode()
            reply = QMessageBox.question(
                self, "Confirm Bulk Import",
                f"Are you sure you want to import {len(self.validation_summary['valid_records'])} product records into the live database?\nMode: {mode}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

            try:
                res = self.import_service.validate_and_import(
                    file_path=self.selected_file_path,
                    mode=mode,
                    commit=True,
                    user_id=self.user_id
                )
                QMessageBox.information(
                    self, "Import Successful",
                    f"Catalog import completed!\n\nAdded: {res['added']}\nUpdated: {res['updated']}\nSkipped: {res['skipped']}\nTotal: {res['total_rows']}"
                )
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Database transaction rolled back. Error:\n{str(e)}")

    class ProductManagementScreen(QWidget):
        def __init__(self, catalog_repo, inventory_repo, user_id=1, parent=None):
            super().__init__(parent)
            self.catalog_repo = catalog_repo
            self.inventory_repo = inventory_repo
            self.user_id = user_id
            self.row_map = []
            self.init_ui()
            self.load_products()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            # Top Filter and Search Bar
            top_box = QHBoxLayout()
            title = QLabel("Product Catalogue & Stock (پراڈکٹ کیٹلاگ و سٹاک)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            top_box.addWidget(title)
            top_box.addStretch()

            # Category filter
            self.cat_filter = QComboBox()
            self.cat_filter.addItem("All Categories (تمام کیٹگریز)", None)
            cats = self.catalog_repo.get_categories(only_active=False)
            for c in cats:
                self.cat_filter.addItem(f"{c.name}", c.id)
            self.cat_filter.currentIndexChanged.connect(self.load_products)
            top_box.addWidget(self.cat_filter)

            # Status filter
            self.status_filter = QComboBox()
            self.status_filter.addItem("Active Only (صرف فعال)", 1)
            self.status_filter.addItem("All Items (تمام اشیاء)", 2)
            self.status_filter.addItem("Inactive Only (غیر فعال)", 3)
            self.status_filter.currentIndexChanged.connect(self.load_products)
            top_box.addWidget(self.status_filter)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search Name, Urdu, SKU, Barcode...")
            self.search_input.setFixedWidth(240)
            self.search_input.textChanged.connect(self.load_products)
            top_box.addWidget(self.search_input)

            layout.addLayout(top_box)

            # Table of Products and Variants
            self.table = QTableWidget()
            self.table.setColumnCount(9)
            self.table.setHorizontalHeaderLabels([
                "Code / SKU", "Barcode", "Category", "Product Name", "Variety / Size", "Unit", "Cost (Rs.)", "Sale Rate (Rs.)", "Stock On-Hand"
            ])
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.doubleClicked.connect(self.on_edit_product)
            layout.addWidget(self.table)

            # Action button bar - First row: Primary Catalog Actions
            btn_box = QHBoxLayout()
            btn_box.setSpacing(8)

            add_prod_btn = QPushButton("➕ Add New Product (نیا پراڈکٹ)")
            add_prod_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 9px 16px; font-size: 13px;")
            add_prod_btn.clicked.connect(self.on_add_product)

            edit_prod_btn = QPushButton("✏️ Edit Product (ترمیم)")
            edit_prod_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 9px 14px;")
            edit_prod_btn.clicked.connect(self.on_edit_product)

            add_fabric_btn = QPushButton("🧵 Add Fabric (تھان/کپڑا)")
            add_fabric_btn.setStyleSheet("background-color: #0d9488; color: white; font-weight: bold; padding: 9px 14px;")
            add_fabric_btn.clicked.connect(self.on_add_fabric)

            variant_btn = QPushButton("🔀 Manage Variants")
            variant_btn.setStyleSheet("background-color: #7c3aed; color: white; font-weight: bold; padding: 9px 14px;")
            variant_btn.clicked.connect(self.on_manage_variants)

            barcode_btn = QPushButton("🏷️ Print Barcode Labels")
            barcode_btn.setStyleSheet("background-color: #d97706; color: white; font-weight: bold; padding: 9px 14px;")
            barcode_btn.clicked.connect(self.on_print_barcode)

            quick_price_btn = QPushButton("📦 Quick Stock & Price (F2)")
            quick_price_btn.setStyleSheet("background-color: #475569; color: white; font-weight: bold; padding: 9px 14px;")
            quick_price_btn.clicked.connect(self.on_quick_stock_price)

            deact_btn = QPushButton("🚫 Toggle Active")
            deact_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 9px 14px;")
            deact_btn.clicked.connect(self.on_toggle_active)

            btn_box.addWidget(add_prod_btn)
            btn_box.addWidget(edit_prod_btn)
            btn_box.addWidget(add_fabric_btn)
            btn_box.addWidget(variant_btn)
            btn_box.addWidget(barcode_btn)
            btn_box.addWidget(quick_price_btn)
            btn_box.addWidget(deact_btn)
            btn_box.addStretch()
            layout.addLayout(btn_box)

            # Secondary Action bar: Advanced Fabric & Import/Export
            sub_btn_box = QHBoxLayout()
            add_roll_btn = QPushButton("🧶 Add Fabric Thaan / Roll (تھان داخل کریں)")
            add_roll_btn.clicked.connect(self.on_add_roll)

            import_btn = QPushButton("📥 Bulk Excel/CSV Import (امپورٹ)")
            import_btn.clicked.connect(self.on_bulk_import)

            export_btn = QPushButton("📤 Export Catalog (ایکسپورٹ)")
            export_btn.clicked.connect(self.on_export_catalog)

            sub_btn_box.addWidget(add_roll_btn)
            sub_btn_box.addWidget(import_btn)
            sub_btn_box.addWidget(export_btn)
            sub_btn_box.addStretch()
            layout.addLayout(sub_btn_box)

        def load_products(self):
            search = self.search_input.text().strip()
            cat_id = self.cat_filter.currentData()
            status_choice = self.status_filter.currentData()
            only_active = (status_choice == 1)

            prods = self.catalog_repo.get_products(
                category_id=cat_id,
                search_term=search if search else None,
                only_active=only_active
            )

            if status_choice == 3:
                prods = [p for p in prods if not p.is_active]

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
                barcode = (v.barcode if v and v.barcode else p.barcode) or "-"
                var_desc = v.display_title() if v else "Standard"
                cost = v.cost_price if v else p.base_cost_price
                price = v.selling_price if v else p.base_selling_price
                stock = v.stock_quantity if v else Decimal("0.000")

                name_display = p.name
                if p.name_urdu:
                    name_display += f" ({p.name_urdu})"

                self.table.setItem(i, 0, QTableWidgetItem(sku))
                self.table.setItem(i, 1, QTableWidgetItem(barcode))
                self.table.setItem(i, 2, QTableWidgetItem(p.category_name or ""))
                self.table.setItem(i, 3, QTableWidgetItem(name_display))
                self.table.setItem(i, 4, QTableWidgetItem(var_desc))
                self.table.setItem(i, 5, QTableWidgetItem(p.unit_name or "Pcs"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{cost:,.2f}"))
                self.table.setItem(i, 7, QTableWidgetItem(f"{price:,.2f}"))
                self.table.setItem(i, 8, QTableWidgetItem(f"{stock:g}"))

                if not p.is_active:
                    for col in range(9):
                        item = self.table.item(i, col)
                        if item:
                            item.setForeground(QColor("#94a3b8"))

        def on_add_product(self):
            dlg = ProductFormDialog(self.catalog_repo, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_products()

        def on_edit_product(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Product", "Please select a product row to edit.")
                return
            p, v = self.row_map[row]
            dlg = ProductFormDialog(self.catalog_repo, product=p, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_products()

        def on_manage_variants(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Product", "Please select a product to manage its variants.")
                return
            p, v = self.row_map[row]
            dlg = VariantManagerDialog(self.catalog_repo, product=p, user_id=self.user_id, parent=self)
            dlg.exec()
            self.load_products()

        def on_print_barcode(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Product", "Please select a product to print barcode labels.")
                return
            p, v = self.row_map[row]
            dlg = BarcodeLabelDialog(product=p, variant=v, parent=self)
            dlg.exec()

        def on_quick_stock_price(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Item", "Please select a row to configure stock and prices.")
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
                else:
                    self.catalog_repo.update_product(
                        product_id=p.id,
                        category_id=p.category_id,
                        subcategory_id=p.subcategory_id,
                        code=p.code,
                        barcode=p.barcode,
                        name=p.name,
                        name_urdu=p.name_urdu,
                        unit_id=p.unit_id,
                        is_fabric=p.is_fabric,
                        min_stock_alert=p.min_stock_alert,
                        base_cost_price=new_cost,
                        base_selling_price=new_price,
                        description=p.description,
                        is_active=p.is_active,
                        stock_quantity=new_stock
                    )
                self.load_products()

        def on_toggle_active(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Product", "Please select a product to toggle active/inactive.")
                return
            p, v = self.row_map[row]
            if p.is_active:
                reply = QMessageBox.question(
                    self, "Deactivate Product",
                    f"Deactivating '{p.name}' will hide it from the billing screen while preserving all historical sales records.\nProceed?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.catalog_repo.deactivate_product(p.id)
            else:
                self.catalog_repo.activate_product(p.id)
            self.load_products()

        def on_add_fabric(self):
            """Opens ProductFormDialog pre-configured for fabric by meter/gaz."""
            dlg = ProductFormDialog(self.catalog_repo, user_id=self.user_id, parent=self)
            dlg.rb_fabric.setChecked(True)
            if dlg.exec() == QDialog.Accepted:
                self.load_products()

        def on_add_roll(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.row_map):
                QMessageBox.information(self, "Select Fabric", "Please select a fabric product row to register a new thaan / roll.")
                return
            p, v = self.row_map[row]
            if not p.is_fabric:
                QMessageBox.warning(self, "Not a Fabric", f"'{p.name}' is sold as piece/set, not fabric by meter/yard.")
                return

            dlg = FabricRollDialog(p, v, parent=self)
            if dlg.exec() == QDialog.Accepted:
                roll_num = dlg.num_input.text().strip() or "TH-UNKNOWN"
                initial_len = to_qty_decimal(dlg.length_spin.value())
                cost = to_decimal(dlg.cost_spin.value())
                notes = dlg.notes_input.text().strip()

                roll = FabricRoll(
                    id=None,
                    product_id=p.id,
                    variant_id=v.id if v else None,
                    roll_number=roll_num,
                    initial_length=initial_len,
                    current_length=initial_len,
                    unit_name=p.unit_name or "Meter",
                    cost_per_unit=cost,
                    notes=notes
                )
                self.inventory_repo.add_fabric_roll(roll)
                QMessageBox.information(self, "Fabric Roll Registered", f"New Thaan #{roll_num} ({initial_len:g} {p.unit_name}) registered successfully!")
                self.load_products()

        def on_bulk_import(self):
            dlg = BulkImportDialog(self.catalog_repo.conn, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_products()

        def on_export_catalog(self):
            dest, _ = QFileDialog.getSaveFileName(self, "Export Product Catalog", "arooj_catalog_export.csv", "CSV (*.csv)")
            if dest:
                svc = ImportExportService(self.catalog_repo.conn)
                svc.export_catalog_to_csv(dest)
                QMessageBox.information(self, "Export Completed", f"Product catalog exported successfully to:\n{dest}")
else:
    class ProductManagementScreen:
        pass
