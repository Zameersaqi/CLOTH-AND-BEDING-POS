"""
Dedicated Inventory & Stock Management Screen for Arooj POS
Phase 4 & Phase 5:
- Real-time stock tracking with decimal quantities (meter/gaz)
- Valuation at Cost and Retail
- Manual Stock Adjustments with mandatory audit reasons
- Low-Stock Alerts and Comparison vs reorder threshold
- Supplier Reorder List preparation and export
- Stock movement history inspection
"""

import csv
from decimal import Decimal
from typing import Optional, List
from pathlib import Path

from app.config import format_currency, to_decimal, to_qty_decimal
from app.models.entities import FabricRoll

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
        QPushButton, QLineEdit, QComboBox, QHeaderView, QMessageBox, QDialog,
        QDoubleSpinBox, QFormLayout, QFileDialog, QRadioButton, QButtonGroup,
        QFrame, QGroupBox, QSplitter
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    QWidget = object

if PYSIDE_AVAILABLE:
    class StockAdjustmentDialog(QDialog):
        """Allows authorized staff to make an auditable stock adjustment with a mandatory reason."""
        def __init__(self, item_dict, inventory_repo, user_id=1, parent=None):
            super().__init__(parent)
            self.item = item_dict
            self.inventory_repo = inventory_repo
            self.user_id = user_id
            self.setWindowTitle(f"Stock Adjustment: {self.item['product_name']}")
            self.resize(460, 420)
            self.init_ui()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setSpacing(12)

            # Item Summary Box
            info_frame = QFrame()
            info_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px;")
            info_layout = QVBoxLayout(info_frame)

            var_title = f"{self.item['size'] or ''} {self.item['color'] or ''}".strip() or "Standard"
            curr_stock = self.item['stock_quantity']
            unit = self.item['unit_name']

            info_layout.addWidget(QLabel(f"<b>Product:</b> {self.item['product_name']} ({var_title})"))
            info_layout.addWidget(QLabel(f"<b>SKU:</b> {self.item['sku']} | <b>Current Stock:</b> <span style='color:#064e3b; font-weight:bold;'>{curr_stock:g} {unit}</span>"))
            layout.addWidget(info_frame)

            form = QFormLayout()

            # Adjustment Direction
            dir_box = QHBoxLayout()
            self.rb_add = QRadioButton("Add Stock (+) [اضافہ]")
            self.rb_deduct = QRadioButton("Deduct Stock (-) [کمی]")
            self.rb_deduct.setChecked(True)

            self.dir_group = QButtonGroup(self)
            self.dir_group.addButton(self.rb_add, 1)
            self.dir_group.addButton(self.rb_deduct, 2)
            dir_box.addWidget(self.rb_deduct)
            dir_box.addWidget(self.rb_add)
            form.addRow("Adjustment Action*:", dir_box)

            # Adjustment Quantity
            self.qty_spin = QDoubleSpinBox()
            self.qty_spin.setRange(0.001, 100000.0)
            self.qty_spin.setDecimals(3 if self.item['is_fabric'] else 0)
            self.qty_spin.setValue(1.0)
            form.addRow(f"Adjustment Quantity ({unit})*:", self.qty_spin)

            # Mandatory Reason Dropdown
            self.reason_combo = QComboBox()
            self.reason_combo.addItems([
                "Physical Count Difference (سٹاک گنتی کا فرق)",
                "Damaged or Defective Goods (خراب یا عیب دار مال)",
                "Returned to Mill / Supplier (مل یا سپلائر کو واپسی)",
                "Theft, Pilferage or Loss (چوری یا گمشدگی)",
                "Fabric Cut Remnant Wastage (تھان کٹنگ کا کٹرا)",
                "Customer Return Restocking (گاہک واپسی درستگی)",
                "Internal Shop Use / Display (دکان کا استعمال / ڈسپلے)",
                "Other (دیگر وجہ - ریمارکس لکھیں)"
            ])
            form.addRow("Mandatory Reason*:", self.reason_combo)

            # Remarks / Notes
            self.notes_input = QLineEdit()
            self.notes_input.setPlaceholderText("Detailed explanation (ضروری وضاحت لکھیں)...")
            form.addRow("Remarks / Notes*:", self.notes_input)

            layout.addLayout(form)

            # Action Buttons
            btn_box = QHBoxLayout()
            cancel = QPushButton("Cancel")
            cancel.clicked.connect(self.reject)

            save = QPushButton("Apply Adjustment (محفوظ کریں)")
            save.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px;")
            save.clicked.connect(self.on_apply)

            btn_box.addWidget(cancel)
            btn_box.addStretch()
            btn_box.addWidget(save)
            layout.addLayout(btn_box)

        def on_apply(self):
            notes = self.notes_input.text().strip()
            reason = self.reason_combo.currentText()
            qty = to_qty_decimal(self.qty_spin.value())

            if not notes:
                QMessageBox.warning(self, "Mandatory Remarks", "Please enter remarks or explanation for this stock adjustment.")
                return

            # Apply sign
            signed_qty = qty if self.rb_add.isChecked() else -qty
            full_reason = f"{reason} - {notes}"

            try:
                self.inventory_repo.adjust_stock(
                    variant_id=self.item["variant_id"],
                    adjustment_qty=signed_qty,
                    reason=full_reason,
                    user_id=self.user_id
                )
                QMessageBox.information(self, "Adjustment Saved", f"Stock adjusted by {signed_qty:+g} {self.item['unit_name']} successfully.")
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to adjust stock: {str(e)}")

    class StockHistoryDialog(QDialog):
        """Displays stock ledger transactions for auditing."""
        def __init__(self, inventory_repo, variant_id=None, parent=None):
            super().__init__(parent)
            self.inventory_repo = inventory_repo
            self.variant_id = variant_id
            self.setWindowTitle("Stock Movement History (سٹاک ٹرانزیکشن ہسٹری)")
            self.resize(800, 500)
            self.init_ui()
            self.load_data()

        def init_ui(self):
            layout = QVBoxLayout(self)

            self.table = QTableWidget()
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels([
                "Date / Time", "Type", "Product Name", "Variety / SKU", "Qty Change", "Unit Cost (Rs.)", "Notes / Reason"
            ])
            self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
            layout.addWidget(self.table)

            close_btn = QPushButton("Close")
            close_btn.clicked.connect(self.accept)
            layout.addWidget(close_btn, alignment=Qt.AlignRight)

        def load_data(self):
            txs = self.inventory_repo.get_stock_transactions(variant_id=self.variant_id)
            self.table.setRowCount(len(txs))
            for i, t in enumerate(txs):
                var_desc = f"{t['sku'] or ''} ({t['size'] or ''})".strip()
                qty = t["quantity"]
                qty_str = f"{qty:+g}" if qty else "0"

                self.table.setItem(i, 0, QTableWidgetItem(str(t["created_at"])[:19]))
                self.table.setItem(i, 1, QTableWidgetItem(str(t["transaction_type"]).upper()))
                self.table.setItem(i, 2, QTableWidgetItem(t["product_name"]))
                self.table.setItem(i, 3, QTableWidgetItem(var_desc))

                qty_item = QTableWidgetItem(qty_str)
                if qty and qty > 0:
                    qty_item.setForeground(QColor("#059669"))
                elif qty and qty < 0:
                    qty_item.setForeground(QColor("#dc2626"))
                self.table.setItem(i, 4, qty_item)

                self.table.setItem(i, 5, QTableWidgetItem(f"{t['unit_cost']:,.2f}"))
                self.table.setItem(i, 6, QTableWidgetItem(t["notes"] or "-"))

    class InventoryScreen(QWidget):
        def __init__(self, inventory_repo, catalog_repo=None, parent=None, **kwargs):
            super().__init__(parent)
            self.inventory_repo = inventory_repo
            self.catalog_repo = catalog_repo
            self.user_id = kwargs.get("user_id", 1)
            self.items = []
            self.init_ui()
            self.load_data()

        def init_ui(self):
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            # Top Title & Direct Add Action Bar
            top_bar = QHBoxLayout()
            title = QLabel("Inventory Management & Valuation (سٹاک کنٹرول و تخمینہ مال)")
            title.setStyleSheet("font-size: 18px; font-weight: 800; color: #064e3b;")
            top_bar.addWidget(title)
            top_bar.addStretch()

            add_btn = QPushButton("➕ Add New Product (نیا پراڈکٹ)")
            add_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 16px; font-size: 13px; border-radius: 6px;")
            add_btn.clicked.connect(self.on_add_product)
            top_bar.addWidget(add_btn)

            bulk_import_btn = QPushButton("📥 Bulk Import (Excel/CSV)")
            bulk_import_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 14px; font-size: 12px; border-radius: 6px;")
            bulk_import_btn.clicked.connect(self.on_bulk_import)
            top_bar.addWidget(bulk_import_btn)

            layout.addLayout(top_bar)

            # Top Summary Valuation Bar
            self.val_frame = QFrame()
            self.val_frame.setStyleSheet("background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px;")
            val_layout = QHBoxLayout(self.val_frame)

            self.lbl_items = QLabel("<b>Items:</b> 0")
            self.lbl_units = QLabel("<b>Total Units:</b> 0")
            self.lbl_cost = QLabel("<b>Cost Valuation:</b> Rs. 0.00")
            self.lbl_retail = QLabel("<b>Retail Valuation:</b> Rs. 0.00")
            self.lbl_low = QLabel("<b>Low Stock Alerts:</b> 0")
            self.lbl_low.setStyleSheet("color: #b45309; font-weight: bold;")

            for lbl in [self.lbl_items, self.lbl_units, self.lbl_cost, self.lbl_retail, self.lbl_low]:
                lbl.setStyleSheet("font-size: 13px;")
                val_layout.addWidget(lbl)
                val_layout.addStretch()

            layout.addWidget(self.val_frame)

            # Filter Controls
            filter_box = QHBoxLayout()

            self.stock_filter = QComboBox()
            self.stock_filter.addItem("All Items (تمام سٹاک)", "all")
            self.stock_filter.addItem("⚠️ Low Stock Only (کم سٹاک والے)", "low_stock")
            self.stock_filter.addItem("❌ Out of Stock (ختم شدہ)", "out_of_stock")
            self.stock_filter.addItem("✅ In Stock (صحت مند سٹاک)", "in_stock")
            self.stock_filter.currentIndexChanged.connect(self.load_data)
            filter_box.addWidget(self.stock_filter)

            self.cat_filter = QComboBox()
            self.cat_filter.addItem("All Categories", None)
            if self.catalog_repo:
                cats = self.catalog_repo.get_categories(only_active=False)
                for c in cats:
                    self.cat_filter.addItem(c.name, c.id)
            self.cat_filter.currentIndexChanged.connect(self.load_data)
            filter_box.addWidget(self.cat_filter)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search SKU, Barcode, Product Name...")
            self.search_input.setFixedWidth(260)
            self.search_input.textChanged.connect(self.load_data)
            filter_box.addWidget(self.search_input)

            filter_box.addStretch()
            layout.addLayout(filter_box)

            # Main Inventory Table
            self.table = QTableWidget()
            self.table.setColumnCount(10)
            self.table.setHorizontalHeaderLabels([
                "SKU", "Product Name", "Variety / Size", "Unit", "On-Hand Stock", "Min Alert", "Cost (Rs.)", "Sale (Rs.)", "Cost Valuation", "Status"
            ])
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            layout.addWidget(self.table)

            # Bottom Action Buttons
            btn_box = QHBoxLayout()
            edit_btn = QPushButton("✏️ Edit Product (ترمیم)")
            edit_btn.setStyleSheet("background-color: #475569; color: white; font-weight: bold; padding: 10px 14px; font-size: 13px; border-radius: 6px;")
            edit_btn.clicked.connect(self.on_edit_product)

            adjust_btn = QPushButton("📋 Stock Adjustment (سٹاک درستگی)")
            adjust_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 10px 16px; font-size: 13px; border-radius: 6px;")
            adjust_btn.clicked.connect(self.on_adjust_stock)

            history_btn = QPushButton("📜 Movement History (ہسٹری)")
            history_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 10px 14px; border-radius: 6px;")
            history_btn.clicked.connect(self.on_view_history)

            reorder_btn = QPushButton("📑 Reorder List (آرڈر لسٹ)")
            reorder_btn.setStyleSheet("background-color: #d97706; color: white; font-weight: bold; padding: 10px 14px; border-radius: 6px;")
            reorder_btn.clicked.connect(self.on_prepare_reorder_list)

            export_btn = QPushButton("📤 Export Inventory (.csv / .xlsx)")
            export_btn.clicked.connect(self.on_export_inventory)

            btn_box.addWidget(edit_btn)
            btn_box.addWidget(adjust_btn)
            btn_box.addWidget(history_btn)
            btn_box.addWidget(reorder_btn)
            btn_box.addWidget(export_btn)
            btn_box.addStretch()
            layout.addLayout(btn_box)

        def load_data(self):
            search = self.search_input.text().strip() or None
            cat_id = self.cat_filter.currentData()
            s_filter = self.stock_filter.currentData()

            self.items = self.inventory_repo.get_all_inventory_items(
                search=search,
                category_id=cat_id,
                stock_filter=s_filter if s_filter != "all" else None
            )

            # Update valuation indicators
            totals = self.inventory_repo.get_inventory_valuation()
            low_items = self.inventory_repo.get_low_stock_items()

            self.lbl_items.setText(f"<b>Items in List:</b> {len(self.items)}")
            self.lbl_units.setText(f"<b>Total Stock Units:</b> {totals['total_items']:g}")
            self.lbl_cost.setText(f"<b>Cost Valuation:</b> Rs. {totals['total_cost_valuation']:,.2f}")
            self.lbl_retail.setText(f"<b>Retail Valuation:</b> Rs. {totals['total_retail_valuation']:,.2f}")
            self.lbl_low.setText(f"<b>Low Stock Alerts:</b> {len(low_items)}")
            if len(low_items) > 0:
                self.lbl_low.setStyleSheet("color: #dc2626; font-weight: bold; font-size: 13px;")

            self.table.setRowCount(len(self.items))
            for i, it in enumerate(self.items):
                var_str = f"{it['size'] or ''} {it['color'] or ''}".strip() or "Standard"
                stock = it["stock_quantity"]
                alert = it["min_stock_alert"]

                self.table.setItem(i, 0, QTableWidgetItem(it["sku"]))
                self.table.setItem(i, 1, QTableWidgetItem(it["product_name"]))
                self.table.setItem(i, 2, QTableWidgetItem(var_str))
                self.table.setItem(i, 3, QTableWidgetItem(it["unit_name"]))

                stock_item = QTableWidgetItem(f"{stock:g}")
                font = stock_item.font()
                font.setBold(True)
                stock_item.setFont(font)
                self.table.setItem(i, 4, stock_item)

                self.table.setItem(i, 5, QTableWidgetItem(f"{alert:g}"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{it['cost_price']:,.2f}"))
                self.table.setItem(i, 7, QTableWidgetItem(f"{it['selling_price']:,.2f}"))
                self.table.setItem(i, 8, QTableWidgetItem(f"{it['cost_valuation']:,.2f}"))

                # Status label
                if stock <= 0:
                    status_lbl = "OUT OF STOCK"
                    color = "#dc2626"
                elif stock <= alert:
                    status_lbl = "LOW STOCK"
                    color = "#d97706"
                else:
                    status_lbl = "IN STOCK"
                    color = "#059669"

                s_item = QTableWidgetItem(status_lbl)
                s_item.setForeground(QColor(color))
                self.table.setItem(i, 9, s_item)

        def on_adjust_stock(self):
            row = self.table.currentRow()
            if row < 0 or row >= len(self.items):
                QMessageBox.information(self, "Select Item", "Please select an inventory item to adjust stock.")
                return
            it = self.items[row]
            dlg = StockAdjustmentDialog(it, self.inventory_repo, user_id=self.user_id, parent=self)
            if dlg.exec() == QDialog.Accepted:
                self.load_data()

        def on_view_history(self):
            row = self.table.currentRow()
            v_id = self.items[row]["variant_id"] if (row >= 0 and row < len(self.items)) else None
            dlg = StockHistoryDialog(self.inventory_repo, variant_id=v_id, parent=self)
            dlg.exec()

        def on_prepare_reorder_list(self):
            reorder_items = self.inventory_repo.get_reorder_list()
            if not reorder_items:
                QMessageBox.information(self, "Stock Level Healthy", "All inventory items are currently above their reorder thresholds!")
                return

            dest, _ = QFileDialog.getSaveFileName(
                self, "Export Supplier Reorder List", "Supplier_Reorder_Order_List.csv", "CSV Files (*.csv)"
            )
            if not dest:
                return

            with open(dest, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Product Code", "Product Name", "Variety / Size", "Unit",
                    "Current On-Hand Stock", "Reorder Threshold", "Suggested Reorder Qty", "Last Cost Price (Rs.)", "Est. Order Cost (Rs.)"
                ])
                total_est_cost = Decimal("0.00")
                for r in reorder_items:
                    rec_qty = max(Decimal("10.000"), to_qty_decimal(r["recommended_order_qty"]))
                    cost = to_decimal(r["cost_price"])
                    line_cost = rec_qty * cost
                    total_est_cost += line_cost

                    writer.writerow([
                        r["sku"],
                        r["product_name"],
                        f"{r['size'] or ''} {r['color'] or ''}".strip() or "Standard",
                        r["unit_name"],
                        f"{r['stock_quantity']:g}",
                        f"{r['min_stock_alert']:g}",
                        f"{rec_qty:g}",
                        f"{cost:.2f}",
                        f"{line_cost:.2f}"
                    ])
                writer.writerow([])
                writer.writerow(["", "", "", "", "", "", "TOTAL ESTIMATED PURCHASE COST:", "", f"{total_est_cost:.2f}"])

            QMessageBox.information(
                self, "Reorder List Ready",
                f"Generated supplier reorder list with {len(reorder_items)} items requiring replenishment!\nSaved to:\n{dest}"
            )

        def on_export_inventory(self):
            dest, _ = QFileDialog.getSaveFileName(
                self, "Export Inventory Valuation", "Inventory_Valuation_Report.csv", "CSV Files (*.csv)"
            )
            if not dest:
                return

            with open(dest, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "SKU", "Product Name", "Urdu Name", "Category", "Variety / Size",
                    "Unit", "On-Hand Stock", "Cost Price", "Sale Price", "Cost Valuation", "Retail Valuation"
                ])
                for it in self.items:
                    writer.writerow([
                        it["sku"],
                        it["product_name"],
                        it["name_urdu"] or "",
                        it["category_name"],
                        f"{it['size'] or ''} {it['color'] or ''}".strip() or "Standard",
                        it["unit_name"],
                        f"{it['stock_quantity']:g}",
                        f"{it['cost_price']:.2f}",
                        f"{it['selling_price']:.2f}",
                        f"{it['cost_valuation']:.2f}",
                        f"{it['retail_valuation']:.2f}"
                    ])

            QMessageBox.information(self, "Export Complete", f"Inventory report saved successfully to:\n{dest}")

        def on_add_product(self):
            """Manual 1-by-1 product addition modal dialog."""
            if not self.catalog_repo:
                QMessageBox.warning(self, "Unavailable", "Catalog repository is not configured.")
                return
            try:
                from app.ui.product_management import ProductFormDialog
                dlg = ProductFormDialog(self.catalog_repo, user_id=self.user_id, parent=self)
                if dlg.exec():
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open Add Product dialog: {str(e)}")

        def on_edit_product(self):
            """Manual 1-by-1 product editing modal dialog."""
            row = self.table.currentRow()
            if row < 0 or row >= len(self.items):
                QMessageBox.information(self, "Select Product", "Please select a product row from the table to edit.")
                return
            it = self.items[row]
            if not self.catalog_repo:
                return
            prod = self.catalog_repo.get_product_by_id(it["product_id"])
            if not prod:
                QMessageBox.warning(self, "Not Found", "Could not locate product record.")
                return
            try:
                from app.ui.product_management import ProductFormDialog
                dlg = ProductFormDialog(self.catalog_repo, product=prod, user_id=self.user_id, parent=self)
                if dlg.exec():
                    self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not open Edit Product dialog: {str(e)}")

        def on_bulk_import(self):
            """Bulk product import from CSV or Excel (.xlsx) file."""
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Excel or CSV File for Bulk Import", "",
                "Spreadsheet Files (*.xlsx *.xls *.csv);;Excel Files (*.xlsx);;CSV Files (*.csv)"
            )
            if not file_path:
                return

            from app.services.import_export_service import ImportExportService
            svc = ImportExportService(self.inventory_repo.conn)

            try:
                # Preview and import with conflict resolution: update_existing
                results = svc.import_file(file_path, mode="update_existing", user_id=self.user_id)
                msg = (
                    f"Bulk Import Complete!\n\n"
                    f"• Processed Rows: {results['total_rows']}\n"
                    f"• New Products Added: {results['added']}\n"
                    f"• Existing Updated: {results['updated']}\n"
                    f"• Skipped / Unchanged: {results['skipped']}\n"
                    f"• Errors / Failed: {len(results['errors'])}"
                )
                if results['errors']:
                    msg += f"\n\nFirst error: {results['errors'][0]}"
                QMessageBox.information(self, "Bulk Import Finished", msg)
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Failed to import bulk spreadsheet:\n{str(e)}")

else:
    class InventoryScreen:
        def __init__(self, inventory_repo, catalog_repo=None, parent=None, **kwargs):
            self.inventory_repo = inventory_repo
            self.catalog_repo = catalog_repo
            self.parent = parent
