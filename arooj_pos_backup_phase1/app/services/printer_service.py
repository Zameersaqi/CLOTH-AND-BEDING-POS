"""
Thermal Printer & Receipt Service for Arooj Cloth and Bedsheet Parda
Supports 58mm (32 columns) and 80mm (48 columns) paper formats, ESC/POS byte sequences,
formatted plain text, and HTML receipts for preview and Windows spooler printing.
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from app.config import format_currency, to_decimal

class PrinterService:
    def __init__(self, paper_width: str = "80mm"):
        self.paper_width = paper_width
        self.cols = 48 if paper_width == "80mm" else 32

    def format_plain_receipt(self, sale_data: dict, settings: Dict[str, str]) -> str:
        """
        Builds a cleanly formatted, monospaced thermal receipt string aligned for 58mm or 80mm.
        """
        c = self.cols
        line_sep = "=" * c
        dash_sep = "-" * c

        shop_name = settings.get("shop_name", "Arooj Cloth and Bedsheet Parda")
        shop_urdu = settings.get("shop_name_urdu", "عروج کلوتھ اینڈ بیڈ شیٹ پردہ")
        address = settings.get("shop_address", "Main Bazaar, Pakistan")
        phone = settings.get("shop_phone", "0300-1234567")
        footer = settings.get("receipt_footer_text", "Thank you for shopping!\nExchange within 7 days.")

        out = []
        out.append(shop_name.center(c))
        if shop_urdu:
            out.append(shop_urdu.center(c))
        out.append(address.center(c))
        out.append(f"Phone: {phone}".center(c))
        out.append(line_sep)

        inv_no = sale_data.get("invoice_number", "")
        dt = str(sale_data.get("sale_date", ""))
        cashier = sale_data.get("cashier_name", "Counter")
        customer = sale_data.get("customer_name", "Walk-in Customer")

        out.append(f"Invoice : {inv_no}".ljust(c))
        out.append(f"Date    : {dt}".ljust(c))
        out.append(f"Cashier : {cashier}".ljust(c))
        if customer:
            out.append(f"Customer: {customer}".ljust(c))
        out.append(dash_sep)

        # Table Header
        if self.paper_width == "80mm":
            # 48 cols: Item (22), Qty (6), Rate (10), Total (10)
            out.append(f"{'Item Description':<22}{'Qty':>6}{'Rate':>10}{'Total':>10}")
        else:
            # 32 cols: Item (14), Qty (4), Rate (7), Total (7)
            out.append(f"{'Item':<14}{'Qty':>4}{'Rate':>7}{'Total':>7}")
        out.append(dash_sep)

        items = sale_data.get("items", [])
        for item in items:
            name = item.get("product_name", "")
            var_parts = [item.get("size"), item.get("color")]
            var_str = " ".join([p for p in var_parts if p])
            full_title = f"{name} {var_str}".strip()

            qty_val = item.get("quantity", 0)
            unit = item.get("unit_name", "Pcs")
            price_val = float(item.get("transaction_price", 0))
            total_val = float(item.get("line_total", 0))

            qty_str = f"{qty_val:g}{unit[:2]}"
            rate_str = f"{price_val:,.0f}"
            tot_str = f"{total_val:,.0f}"

            if self.paper_width == "80mm":
                if len(full_title) > 22:
                    out.append(full_title)
                    out.append(f"{'':<22}{qty_str:>6}{rate_str:>10}{tot_str:>10}")
                else:
                    out.append(f"{full_title:<22}{qty_str:>6}{rate_str:>10}{tot_str:>10}")
            else:
                if len(full_title) > 14:
                    out.append(full_title)
                    out.append(f"{'':<14}{qty_str:>4}{rate_str:>7}{tot_str:>7}")
                else:
                    out.append(f"{full_title:<14}{qty_str:>4}{rate_str:>7}{tot_str:>7}")

            if item.get("is_price_overridden"):
                orig = float(item.get("original_catalog_price", 0))
                out.append(f"  *Special rate (Catalog: Rs.{orig:,.0f})")

        out.append(dash_sep)

        subtotal = float(sale_data.get("subtotal", 0))
        discount = float(sale_data.get("discount_amount", 0))
        tax = float(sale_data.get("tax_amount", 0))
        grand_total = float(sale_data.get("grand_total", 0))
        paid = float(sale_data.get("paid_amount", 0))
        balance = float(sale_data.get("balance_amount", 0))

        def fmt_row(label: str, val: float) -> str:
            val_s = f"Rs. {val:,.2f}"
            return f"{label:<{c - len(val_s)}}{val_s}"

        out.append(fmt_row("Subtotal:", subtotal))
        if discount > 0:
            out.append(fmt_row("Discount:", -discount))
        if tax > 0:
            out.append(fmt_row("Tax:", tax))
        out.append(line_sep)
        out.append(fmt_row("GRAND TOTAL:", grand_total))
        out.append(fmt_row("Paid Amount:", paid))
        if balance > 0:
            out.append(fmt_row("Balance Due:", balance))

        payments = sale_data.get("payments", [])
        if payments:
            change = float(payments[0].get("change_returned", 0))
            if change > 0:
                out.append(fmt_row("Change Given:", change))

        out.append(line_sep)
        for fl in footer.split("\n"):
            out.append(fl.center(c))
        out.append("\n" + "=" * c)
        return "\n".join(out)

    def generate_html_receipt(self, sale_data: dict, settings: Dict[str, str]) -> str:
        """Generates an HTML receipt styled for high-resolution thermal rendering or browser print."""
        text_receipt = self.format_plain_receipt(sale_data, settings)
        shop_name = settings.get("shop_name", "Arooj Cloth and Bedsheet Parda")
        logo_path = settings.get("shop_logo_path", "")

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Receipt {sale_data.get('invoice_number', '')}</title>
    <style>
        body {{
            font-family: 'Courier New', Courier, monospace;
            background-color: #f7f7f7;
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
        }}
        .receipt-container {{
            background: #ffffff;
            width: {'380px' if self.paper_width == '80mm' else '280px'};
            padding: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-radius: 4px;
            white-space: pre-wrap;
            font-size: {'13px' if self.paper_width == '80mm' else '11px'};
            line-height: 1.4;
            color: #111;
        }}
        @media print {{
            body {{ background: transparent; padding: 0; }}
            .receipt-container {{ box-shadow: none; padding: 0; width: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="receipt-container">{text_receipt}</div>
</body>
</html>"""
