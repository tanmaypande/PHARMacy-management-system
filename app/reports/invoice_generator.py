"""
Invoice and Thermal Receipt Generator for MediCare PMS.
Generates formatted clinical receipts and POS slips for patient handout and auditing.
"""
from datetime import datetime
from typing import Dict, Any, List


class InvoiceGenerator:
    @staticmethod
    def generate_ascii_receipt(sale_dict: Dict[str, Any]) -> str:
        """
        Generates a standard formatted 80-column / 42-column pharmacy receipt slip.
        """
        inv_no = sale_dict.get("invoice_number", "INV-UNKNOWN")
        dt_str = sale_dict.get("created_at", "")
        if "T" in dt_str:
            try:
                dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                dt_formatted = dt_obj.strftime("%d %b %Y, %I:%M %p")
            except Exception:
                dt_formatted = dt_str
        else:
            dt_formatted = dt_str or datetime.now().strftime("%d %b %Y, %I:%M %p")

        cust_name = sale_dict.get("customer_name") or "Walk-in Customer"
        cust_phone = sale_dict.get("customer_phone") or "—"
        cashier = sale_dict.get("cashier_name") or "Pharmacist"
        payment_method = sale_dict.get("payment_method") or "Cash"

        lines = [
            "=" * 46,
            "         MEDICARE PHARMACY & CLINIC          ",
            "     Licensed Pharmaceutical Dispensary      ",
            "         Tel: +1 (555) 019-2834              ",
            "=" * 46,
            f" Invoice No : {inv_no}",
            f" Date/Time  : {dt_formatted}",
            f" Cashier    : {cashier}",
            f" Patient    : {cust_name}",
            f" Contact    : {cust_phone}",
            "-" * 46,
            f"{'Item / Lot':<24} {'Qty':>4} {'Price':>7} {'Total':>8}",
            "-" * 46,
        ]

        items: List[Dict[str, Any]] = sale_dict.get("items", [])
        for it in items:
            med_name = it.get("medicine_name", "Medicine")[:22]
            batch_no = it.get("batch_number", "")
            exp_date = str(it.get("expiry_date", ""))
            qty = it.get("quantity", 1)
            price = float(it.get("unit_price", 0))
            subtotal = float(it.get("subtotal", 0))

            lines.append(f"{med_name:<24} {qty:>4} {price:>7.2f} {subtotal:>8.2f}")
            lines.append(f"  Lot: {batch_no} (Exp: {exp_date})")

        subtotal_val = float(sale_dict.get("subtotal", 0))
        discount_val = float(sale_dict.get("discount_amount", 0))
        tax_val = float(sale_dict.get("tax_amount", 0))
        total_val = float(sale_dict.get("total_amount", 0))

        lines.extend([
            "-" * 46,
            f"{'Subtotal:':<30} ${subtotal_val:>13.2f}",
        ])

        if discount_val > 0:
            pct = sale_dict.get("discount_percent", 0)
            lines.append(f"{f'Discount ({pct}%):':<30} -${discount_val:>12.2f}")

        if tax_val > 0:
            pct = sale_dict.get("tax_percent", 0)
            lines.append(f"{f'Tax / GST ({pct}%):':<30} +${tax_val:>12.2f}")

        lines.extend([
            "=" * 46,
            f"{'GRAND TOTAL:':<28} ${total_val:>15.2f}",
            f"{'Payment Tendered:':<28} {payment_method:>16}",
            "=" * 46,
            "        THANK YOU FOR TRUSTING MEDICARE       ",
            "   Please keep this receipt for prescription  ",
            "              records & refills               ",
            "=" * 46,
        ])

        return "\n".join(lines)
