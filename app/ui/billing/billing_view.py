"""
Commercial Point of Sale (POS) & Clinical Billing Module for MediCare PMS.
Enforces TQM Safeguards:
- Complete itemized bill generation with batch lot deduction
- Clinical safety blocks preventing expired lot dispensing
- Real-time customer receipt visualization and printing
- Real-time financial calculations (exact decimals, tax, discounts)
"""
import os
import tkinter as tk
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
import customtkinter as ctk

from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.badge import StatusBadge
from app.ui.components.stat_card import StatCard
from app.ui.components.data_table import DataTable
from app.reports.invoice_generator import InvoiceGenerator


class CustomerReceiptModal(ctk.CTkToplevel):
    """
    Commercial Customer Receipt Modal.
    Displays a clean, printable medical receipt to show the customer with itemized lots,
    taxes, discounts, and payment verification.
    """
    def __init__(self, master, sale_dict: Dict[str, Any]):
        super().__init__(master)
        self.sale_dict = sale_dict

        inv_no = sale_dict.get("invoice_number", "RECEIPT")
        self.title(f"MediCare Pharmacy — Customer Receipt {inv_no}")
        self.geometry("620x720")
        self.minsize(580, 600)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_receipt()

    def _build_receipt(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Receipt Paper Card (White in light theme, card bg in dark theme)
        card = ctk.CTkFrame(
            container,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER
        )
        card.pack(fill="both", expand=True, pady=(0, 14))

        # 1. Pharmacy Clinic Header
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(16, 8))

        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x")

        logo_box = ctk.CTkFrame(top_row, fg_color=Theme.PRIMARY, width=38, height=38, corner_radius=8)
        logo_box.pack(side="left", padx=(0, 10))
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="🏥", font=accessibility_manager.get_font(20)).pack(expand=True)

        clinic_info = ctk.CTkFrame(top_row, fg_color="transparent")
        clinic_info.pack(side="left")

        ctk.CTkLabel(
            clinic_info,
            text="MEDICARE PHARMACY & HEALTHCARE",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            clinic_info,
            text="Licensed Dispensary • Tel: +1 (555) 019-2834 • License: PH-99201",
            font=accessibility_manager.get_font(10),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        # Status Badge on Top Right
        StatusBadge(top_row, text="PAID IN FULL", variant="success").pack(side="right")

        # Divider
        ctk.CTkFrame(card, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=20, pady=8)

        # 2. Invoice & Patient Metadata Grid
        meta_frame = ctk.CTkFrame(card, fg_color=Theme.BG_MUTED, corner_radius=8)
        meta_frame.pack(fill="x", padx=20, pady=(0, 10))
        meta_frame.grid_columnconfigure((0, 1), weight=1)

        inv_no = self.sale_dict.get("invoice_number", "INV-UNKNOWN")
        dt_str = self.sale_dict.get("created_at", "")
        if "T" in dt_str:
            try:
                dt_obj = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                dt_formatted = dt_obj.strftime("%d %b %Y, %I:%M %p")
            except Exception:
                dt_formatted = dt_str
        else:
            dt_formatted = dt_str or datetime.now().strftime("%d %b %Y, %I:%M %p")

        cust_name = self.sale_dict.get("customer_name") or "Walk-in Patient"
        cust_phone = self.sale_dict.get("customer_phone") or "—"
        cashier = self.sale_dict.get("cashier_name") or "Pharmacist"
        payment_method = self.sale_dict.get("payment_method") or "Cash"

        # Col 0: Invoice & Cashier
        col0 = ctk.CTkFrame(meta_frame, fg_color="transparent")
        col0.grid(row=0, column=0, sticky="w", padx=12, pady=10)
        ctk.CTkLabel(col0, text=f"Invoice No : {inv_no}", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(col0, text=f"Date / Time : {dt_formatted}", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(col0, text=f"Dispenser  : {cashier}", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MUTED).pack(anchor="w")

        # Col 1: Patient info & Tender
        col1 = ctk.CTkFrame(meta_frame, fg_color="transparent")
        col1.grid(row=0, column=1, sticky="w", padx=12, pady=10)
        ctk.CTkLabel(col1, text=f"Patient   : {cust_name}", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        ctk.CTkLabel(col1, text=f"Contact   : {cust_phone}", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(col1, text=f"Tender    : {payment_method}", font=accessibility_manager.get_font(11), text_color=Theme.PRIMARY).pack(anchor="w")

        # 3. Itemized Prescription Table Header
        tbl_hdr = ctk.CTkFrame(card, fg_color=Theme.SECONDARY, height=30, corner_radius=6)
        tbl_hdr.pack(fill="x", padx=20, pady=(4, 2))
        tbl_hdr.pack_propagate(False)

        ctk.CTkLabel(tbl_hdr, text="Item Description & Lot", width=220, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=8)
        ctk.CTkLabel(tbl_hdr, text="Expiry", width=80, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(tbl_hdr, text="Qty", width=45, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(tbl_hdr, text="Price", width=70, anchor="e", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(tbl_hdr, text="Subtotal", width=80, anchor="e", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="right", padx=8)

        # Items Scroll Frame
        items_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent")
        items_scroll.pack(fill="both", expand=True, padx=20, pady=2)

        items = self.sale_dict.get("items", [])
        for it in items:
            row = ctk.CTkFrame(items_scroll, fg_color="transparent")
            row.pack(fill="x", pady=3)

            med_name = it.get("medicine_name", "Medicine")
            batch_no = it.get("batch_number", "")
            exp_date = str(it.get("expiry_date", ""))
            qty = it.get("quantity", 1)
            price = float(it.get("unit_price", 0))
            subtotal = float(it.get("subtotal", 0))

            desc_box = ctk.CTkFrame(row, fg_color="transparent", width=220)
            desc_box.pack(side="left", padx=8)
            ctk.CTkLabel(desc_box, text=med_name, font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN, anchor="w").pack(anchor="w")
            ctk.CTkLabel(desc_box, text=f"Lot: {batch_no}", font=accessibility_manager.get_font(9), text_color=Theme.TEXT_MUTED, anchor="w").pack(anchor="w")

            ctk.CTkLabel(row, text=exp_date, width=80, anchor="center", font=accessibility_manager.get_font(10), text_color=Theme.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=str(qty), width=45, anchor="center", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(row, text=f"${price:.2f}", width=70, anchor="e", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(row, text=f"${subtotal:.2f}", width=80, anchor="e", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="right", padx=8)

        # Divider
        ctk.CTkFrame(card, fg_color=Theme.BORDER, height=1).pack(fill="x", padx=20, pady=6)

        # 4. Financial Calculations Box
        fin_box = ctk.CTkFrame(card, fg_color="transparent")
        fin_box.pack(fill="x", padx=20, pady=(2, 12))

        sub_val = float(self.sale_dict.get("subtotal", 0))
        disc_val = float(self.sale_dict.get("discount_amount", 0))
        disc_pct = self.sale_dict.get("discount_percent", 0)
        tax_val = float(self.sale_dict.get("tax_amount", 0))
        tax_pct = self.sale_dict.get("tax_percent", 0)
        tot_val = float(self.sale_dict.get("total_amount", 0))

        fin_right = ctk.CTkFrame(fin_box, fg_color="transparent")
        fin_right.pack(side="right")

        def _add_fin_line(label: str, amount_str: str, bold=False, color=Theme.TEXT_MAIN):
            f_row = ctk.CTkFrame(fin_right, fg_color="transparent")
            f_row.pack(anchor="e", pady=1)
            ctk.CTkLabel(f_row, text=label, width=140, anchor="e", font=accessibility_manager.get_font(11, weight="bold" if bold else "normal"), text_color=Theme.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(f_row, text=amount_str, width=100, anchor="e", font=accessibility_manager.get_font(12 if not bold else 16, weight="bold" if bold else "normal"), text_color=color).pack(side="right")

        _add_fin_line("Subtotal:", f"${sub_val:.2f}")
        if disc_val > 0:
            _add_fin_line(f"Discount ({disc_pct}%):", f"-${disc_val:.2f}", color=Theme.DANGER_TEXT)
        if tax_val > 0:
            _add_fin_line(f"Tax / GST ({tax_pct}%):", f"+${tax_val:.2f}")

        # Grand Total Pill
        grand_row = ctk.CTkFrame(fin_right, fg_color=Theme.BG_MUTED, corner_radius=8)
        grand_row.pack(anchor="e", pady=(4, 0))
        ctk.CTkLabel(grand_row, text="GRAND TOTAL:", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.PRIMARY).pack(side="left", padx=10, pady=6)
        ctk.CTkLabel(grand_row, text=f"${tot_val:.2f}", font=accessibility_manager.get_font(17, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="right", padx=10, pady=6)

        # 5. Modal Footer Action Buttons
        bot_buttons = ctk.CTkFrame(container, fg_color="transparent")
        bot_buttons.pack(fill="x")

        self.btn_export = ctk.CTkButton(
            bot_buttons,
            text="🖨 Save / Export Receipt",
            height=40,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            font=accessibility_manager.get_font(12, weight="bold"),
            command=self._save_receipt_file
        )
        self.btn_export.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_copy = ctk.CTkButton(
            bot_buttons,
            text="📋 Copy Slip",
            height=40,
            width=110,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MAIN,
            font=accessibility_manager.get_font(12),
            command=self._copy_slip
        )
        self.btn_copy.pack(side="left", padx=6)

        ctk.CTkButton(
            bot_buttons,
            text="Close (Esc)",
            height=40,
            width=100,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(12),
            command=self.destroy
        ).pack(side="right", padx=(6, 0))

    def _save_receipt_file(self):
        inv_no = self.sale_dict.get("invoice_number", "RECEIPT")
        receipt_text = InvoiceGenerator.generate_ascii_receipt(self.sale_dict)
        filename = f"receipt_{inv_no}.txt"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(receipt_text)
            self.btn_export.configure(text=f"✓ Saved ({filename})")
        except Exception as e:
            self.btn_export.configure(text="Error saving receipt")

    def _copy_slip(self):
        receipt_text = InvoiceGenerator.generate_ascii_receipt(self.sale_dict)
        self.clipboard_clear()
        self.clipboard_append(receipt_text)
        self.btn_copy.configure(text="✓ Copied!")


class NewBillModal(ctk.CTkToplevel):
    """
    Comprehensive Point-of-Sale (POS) & Prescription Checkout Dialog.
    Enforces real-time stock validations, clinical expiry blocks, and creates bills atomically.
    """
    def __init__(self, master, api_client: APIClient, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.on_success = on_success

        self.available_batches: List[Dict[str, Any]] = []
        self.cart_items: List[Dict[str, Any]] = []

        self.title("New Prescription Dispensation & Bill (Checkout)")
        self.geometry("860x740")
        self.minsize(780, 640)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-Return>", lambda e: self._complete_sale())

        self._build_ui()
        self._load_batches()

    def _build_ui(self):
        main_box = ctk.CTkFrame(self, fg_color="transparent")
        main_box.pack(fill="both", expand=True, padx=22, pady=18)

        # Header Title
        ctk.CTkLabel(
            main_box,
            text="🧾 Point of Sale & Clinical Dispensation",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            main_box,
            text="TQM Compliance: Expired lots are automatically barred from dispensation.",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 10))

        # Top Section: Patient & Tender Info Card
        cust_card = ctk.CTkFrame(main_box, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        cust_card.pack(fill="x", pady=(0, 10))

        cust_row = ctk.CTkFrame(cust_card, fg_color="transparent")
        cust_row.pack(fill="x", padx=14, pady=10)
        cust_row.grid_columnconfigure((0, 1, 2), weight=1)

        # Patient Name
        col_cname = ctk.CTkFrame(cust_row, fg_color="transparent")
        col_cname.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkLabel(col_cname, text="Patient / Customer Name *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_cust_name = ctk.CTkEntry(col_cname, placeholder_text="Walk-in Patient", height=34, border_color=Theme.BORDER, font=accessibility_manager.get_font(12))
        self.entry_cust_name.pack(fill="x", pady=(2, 0))
        self.entry_cust_name.insert(0, "Walk-in Patient")

        # Patient Phone
        col_cphone = ctk.CTkFrame(cust_row, fg_color="transparent")
        col_cphone.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(col_cphone, text="Phone Number", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_cust_phone = ctk.CTkEntry(col_cphone, placeholder_text="e.g. 555-0199", height=34, border_color=Theme.BORDER, font=accessibility_manager.get_font(12))
        self.entry_cust_phone.pack(fill="x", pady=(2, 0))

        # Tender / Payment Mode
        col_tender = ctk.CTkFrame(cust_row, fg_color="transparent")
        col_tender.grid(row=0, column=2, sticky="ew", padx=(8, 0))
        ctk.CTkLabel(col_tender, text="Payment Method", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.payment_var = ctk.StringVar(value="Cash")
        self.payment_opt = ctk.CTkOptionMenu(
            col_tender,
            variable=self.payment_var,
            values=["Cash", "Credit Card", "Debit Card", "UPI / Digital", "Insurance"],
            height=34,
            font=accessibility_manager.get_font(12)
        )
        self.payment_opt.pack(fill="x", pady=(2, 0))

        # Middle Section: Medicine & Lot Picker Bar
        add_card = ctk.CTkFrame(main_box, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        add_card.pack(fill="x", pady=(0, 10))

        picker_row = ctk.CTkFrame(add_card, fg_color="transparent")
        picker_row.pack(fill="x", padx=14, pady=10)

        # Batch Lot Selection Menu
        col_picker = ctk.CTkFrame(picker_row, fg_color="transparent")
        col_picker.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(col_picker, text="Select Medicine & Lot (Stock > 0 & Non-Expired) *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")

        self.batch_var = ctk.StringVar(value="Loading pharmaceutical inventory...")
        self.batch_opt = ctk.CTkOptionMenu(
            col_picker,
            variable=self.batch_var,
            values=["Loading..."],
            height=34,
            font=accessibility_manager.get_font(11),
            command=self._on_batch_selected
        )
        self.batch_opt.pack(fill="x", pady=(2, 0))

        # Qty Input
        col_qty = ctk.CTkFrame(picker_row, fg_color="transparent", width=80)
        col_qty.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(col_qty, text="Qty *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_qty = ctk.CTkEntry(col_qty, width=75, height=34, border_color=Theme.BORDER, font=accessibility_manager.get_font(12))
        self.entry_qty.pack(pady=(2, 0))
        self.entry_qty.insert(0, "1")

        # Price Input
        col_price = ctk.CTkFrame(picker_row, fg_color="transparent", width=95)
        col_price.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(col_price, text="Price ($)", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_price = ctk.CTkEntry(col_price, width=90, height=34, border_color=Theme.BORDER, font=accessibility_manager.get_font(12))
        self.entry_price.pack(pady=(2, 0))
        self.entry_price.insert(0, "0.00")

        # Add to Cart Button
        col_add_btn = ctk.CTkFrame(picker_row, fg_color="transparent")
        col_add_btn.pack(side="right", padx=(4, 0))
        ctk.CTkLabel(col_add_btn, text=" ", font=accessibility_manager.get_font(11)).pack()
        ctk.CTkButton(
            col_add_btn,
            text="➕ Add to Bill",
            height=34,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            font=accessibility_manager.get_font(11, weight="bold"),
            command=self._add_item_to_cart
        ).pack(pady=(2, 0))

        # Cart Table Section
        cart_frame = ctk.CTkFrame(main_box, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        cart_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Cart Header
        c_hdr = ctk.CTkFrame(cart_frame, fg_color=Theme.SECONDARY, height=32, corner_radius=6)
        c_hdr.pack(fill="x", padx=10, pady=(10, 4))
        c_hdr.pack_propagate(False)

        ctk.CTkLabel(c_hdr, text="Medicine / Item", width=220, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=8)
        ctk.CTkLabel(c_hdr, text="Batch Lot", width=110, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(c_hdr, text="Expiry", width=90, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(c_hdr, text="Qty", width=55, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(c_hdr, text="Price", width=75, anchor="e", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(c_hdr, text="Line Total", width=85, anchor="e", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(c_hdr, text="Action", width=50, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="right", padx=8)

        # Cart Scroll Frame
        self.cart_scroll = ctk.CTkScrollableFrame(cart_frame, fg_color="transparent")
        self.cart_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.lbl_empty_cart = ctk.CTkLabel(
            self.cart_scroll,
            text="No medicines added yet. Select a product above and click 'Add to Bill'.",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_empty_cart.pack(pady=30)

        # Bottom Totals & Actions Card
        bot_card = ctk.CTkFrame(main_box, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        bot_card.pack(fill="x", pady=(0, 6))

        bot_layout = ctk.CTkFrame(bot_card, fg_color="transparent")
        bot_layout.pack(fill="x", padx=14, pady=10)

        # Left side of bottom: Discount and Tax entries
        adjust_box = ctk.CTkFrame(bot_layout, fg_color="transparent")
        adjust_box.pack(side="left")

        # Discount Row
        d_row = ctk.CTkFrame(adjust_box, fg_color="transparent")
        d_row.pack(anchor="w", pady=2)
        ctk.CTkLabel(d_row, text="Discount (%):", width=95, anchor="w", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MAIN).pack(side="left")
        self.entry_disc = ctk.CTkEntry(d_row, width=65, height=28, border_color=Theme.BORDER, font=accessibility_manager.get_font(11))
        self.entry_disc.pack(side="left")
        self.entry_disc.insert(0, "0")
        self.entry_disc.bind("<KeyRelease>", lambda e: self._recalc_totals())

        # Tax Row
        t_row = ctk.CTkFrame(adjust_box, fg_color="transparent")
        t_row.pack(anchor="w", pady=2)
        ctk.CTkLabel(t_row, text="Tax / GST (%):", width=95, anchor="w", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MAIN).pack(side="left")
        self.entry_tax = ctk.CTkEntry(t_row, width=65, height=28, border_color=Theme.BORDER, font=accessibility_manager.get_font(11))
        self.entry_tax.pack(side="left")
        self.entry_tax.insert(0, "0")
        self.entry_tax.bind("<KeyRelease>", lambda e: self._recalc_totals())

        # Right side of bottom: Big Total Pill & Complete Button
        fin_right = ctk.CTkFrame(bot_layout, fg_color="transparent")
        fin_right.pack(side="right")

        self.lbl_subtotal_display = ctk.CTkLabel(
            fin_right,
            text="Subtotal: $0.00",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_subtotal_display.pack(anchor="e")

        self.lbl_net_total = ctk.CTkLabel(
            fin_right,
            text="Payable: $0.00",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.PRIMARY
        )
        self.lbl_net_total.pack(anchor="e", pady=(0, 6))

        # Error text
        self.lbl_error = ctk.CTkLabel(main_box, text="", font=accessibility_manager.get_font(11), text_color=Theme.DANGER_TEXT)
        self.lbl_error.pack(anchor="w", pady=(0, 6))

        # Checkout Buttons
        btn_box = ctk.CTkFrame(main_box, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_checkout = ctk.CTkButton(
            btn_box,
            text="💳 Complete Sale & Print Bill (Ctrl+Enter)",
            height=40,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            font=accessibility_manager.get_font(13, weight="bold"),
            command=self._complete_sale
        )
        self.btn_checkout.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkButton(
            btn_box,
            text="Cancel (Esc)",
            height=40,
            width=110,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(12),
            command=self.destroy
        ).pack(side="right")

    def _load_batches(self):
        run_in_background(
            lambda: self.api_client.get_available_batches_for_sale(),
            on_success=self._populate_batches,
            on_error=lambda e: self._show_error(f"Failed loading inventory batches: {e}")
        )

    def _populate_batches(self, batches: List[Dict[str, Any]]):
        self.available_batches = batches
        if not batches:
            self.batch_opt.configure(values=["No available stock lots found"])
            self.batch_var.set("No available stock lots found")
            return

        options = []
        for b in batches:
            label = f"{b['medicine_name']}  (Lot: {b['batch_number']} | Exp: {b['expiry_date']} | Stock: {b['available_quantity']} | ${b['selling_price']:.2f})"
            options.append(label)

        self.batch_opt.configure(values=options)
        self.batch_var.set(options[0])
        self._on_batch_selected(options[0])

    def _on_batch_selected(self, choice: str):
        idx = self.batch_opt.cget("values").index(choice) if choice in self.batch_opt.cget("values") else -1
        if idx >= 0 and idx < len(self.available_batches):
            b = self.available_batches[idx]
            self.entry_price.delete(0, "end")
            self.entry_price.insert(0, f"{b['selling_price']:.2f}")

    def _add_item_to_cart(self):
        self.lbl_error.configure(text="")
        choice = self.batch_var.get()
        values = self.batch_opt.cget("values")
        if choice not in values or not self.available_batches:
            self._show_error("Please select a valid pharmaceutical batch.")
            return

        idx = values.index(choice)
        batch = self.available_batches[idx]

        try:
            qty = int(self.entry_qty.get().strip())
            if qty <= 0:
                raise ValueError()
        except ValueError:
            self._show_error("Dispensing quantity must be a positive whole number.")
            return

        # Check existing cart quantity + new quantity <= available stock
        existing_in_cart = sum(it["quantity"] for it in self.cart_items if it["batch_id"] == batch["batch_id"])
        if existing_in_cart + qty > batch["available_quantity"]:
            self._show_error(
                f"Insufficient stock: Lot '{batch['batch_number']}' has only {batch['available_quantity']} units. "
                f"You already have {existing_in_cart} in bill."
            )
            return

        try:
            unit_price = float(self.entry_price.get().strip())
            if unit_price < 0:
                raise ValueError()
        except ValueError:
            self._show_error("Unit price must be a valid non-negative number.")
            return

        subtotal = round(qty * unit_price, 2)

        self.cart_items.append({
            "batch_id": batch["batch_id"],
            "medicine_id": batch["medicine_id"],
            "medicine_name": batch["medicine_name"],
            "batch_number": batch["batch_number"],
            "expiry_date": batch["expiry_date"],
            "quantity": qty,
            "unit_price": unit_price,
            "subtotal": subtotal,
        })

        self._render_cart()
        self._recalc_totals()

    def _render_cart(self):
        # Clear previous rows
        for child in self.cart_scroll.winfo_children():
            child.destroy()

        if not self.cart_items:
            self.lbl_empty_cart = ctk.CTkLabel(
                self.cart_scroll,
                text="No medicines added yet. Select a product above and click 'Add to Bill'.",
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MUTED
            )
            self.lbl_empty_cart.pack(pady=30)
            return

        for idx, item in enumerate(self.cart_items):
            row = ctk.CTkFrame(self.cart_scroll, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", pady=2)

            desc = f"{item['medicine_name']}"
            ctk.CTkLabel(row, text=desc, width=220, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=8, pady=4)
            ctk.CTkLabel(row, text=item["batch_number"], width=110, anchor="w", font=accessibility_manager.get_font(10), text_color=Theme.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=str(item["expiry_date"]), width=90, anchor="center", font=accessibility_manager.get_font(10), text_color=Theme.TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(row, text=str(item["quantity"]), width=55, anchor="center", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(row, text=f"${item['unit_price']:.2f}", width=75, anchor="e", font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MAIN).pack(side="left")
            ctk.CTkLabel(row, text=f"${item['subtotal']:.2f}", width=85, anchor="e", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.PRIMARY).pack(side="left")

            ctk.CTkButton(
                row,
                text="✕",
                width=32,
                height=26,
                corner_radius=5,
                fg_color=Theme.DANGER_BG,
                hover_color="#FCA5A5",
                text_color=Theme.DANGER_TEXT,
                font=accessibility_manager.get_font(11, weight="bold"),
                command=lambda i=idx: self._remove_from_cart(i)
            ).pack(side="right", padx=8)

    def _remove_from_cart(self, idx: int):
        if 0 <= idx < len(self.cart_items):
            self.cart_items.pop(idx)
            self._render_cart()
            self._recalc_totals()

    def _recalc_totals(self):
        subtotal = sum(it["subtotal"] for it in self.cart_items)

        try:
            disc_pct = float(self.entry_disc.get().strip() or 0)
        except ValueError:
            disc_pct = 0.0

        try:
            tax_pct = float(self.entry_tax.get().strip() or 0)
        except ValueError:
            tax_pct = 0.0

        disc_amt = round(subtotal * (disc_pct / 100.0), 2)
        taxable = max(0.0, subtotal - disc_amt)
        tax_amt = round(taxable * (tax_pct / 100.0), 2)
        net_total = round(taxable + tax_amt, 2)

        self.lbl_subtotal_display.configure(
            text=f"Subtotal: ${subtotal:.2f}  |  Disc: -${disc_amt:.2f}  |  Tax: +${tax_amt:.2f}"
        )
        self.lbl_net_total.configure(text=f"Payable: ${net_total:.2f}")

    def _complete_sale(self):
        self.lbl_error.configure(text="")
        if not self.cart_items:
            self._show_error("Cannot complete sale: no medicines in bill.")
            return

        cust_name = self.entry_cust_name.get().strip() or "Walk-in Patient"
        cust_phone = self.entry_cust_phone.get().strip() or None
        payment_method = self.payment_var.get()

        try:
            disc_pct = float(self.entry_disc.get().strip() or 0)
            tax_pct = float(self.entry_tax.get().strip() or 0)
        except ValueError:
            self._show_error("Invalid discount or tax percentage.")
            return

        payload = {
            "customer_name": cust_name,
            "customer_phone": cust_phone,
            "payment_method": payment_method,
            "discount_percent": disc_pct,
            "tax_percent": tax_pct,
            "cashier_name": "Pharmacist",
            "items": [
                {
                    "batch_id": it["batch_id"],
                    "quantity": it["quantity"],
                    "unit_price": it["unit_price"]
                }
                for it in self.cart_items
            ]
        }

        self.btn_checkout.configure(state="disabled", text="⏳ Processing Transaction...")

        run_in_background(
            lambda: self.api_client.create_sale(payload),
            on_success=self._on_sale_success,
            on_error=self._on_sale_error
        )

    def _on_sale_success(self, created_sale: Dict[str, Any]):
        self.btn_checkout.configure(state="normal", text="💳 Complete Sale & Print Bill (Ctrl+Enter)")
        if self.on_success:
            self.on_success(created_sale)
        self.destroy()

    def _on_sale_error(self, err_msg: str):
        self.btn_checkout.configure(state="normal", text="💳 Complete Sale & Print Bill (Ctrl+Enter)")
        self._show_error(str(err_msg))

    def _show_error(self, msg: str):
        self.lbl_error.configure(text=f"⚠ {msg}")


class BillingView(ctk.CTkFrame):
    """
    Main Point-of-Sale (POS) & Billing View.
    Replaces the placeholder in MainWindow navigation rail.
    """
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.raw_sales: List[Dict[str, Any]] = []

        self._build_ui()
        self._load_data()

    def _build_ui(self):
        # 1. Action Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🧾 Point of Sale & Clinical Dispensing",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading billing transactions from PostgreSQL...",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_count.pack(anchor="w")

        btn_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=95,
            height=36,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            command=self._load_data,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ New Bill (Ctrl+N)",
            width=150,
            height=36,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_new_bill_modal,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        # 2. KPI Summary Cards (Revenue, Bills, Units)
        cards_row = ctk.CTkFrame(self, fg_color="transparent")
        cards_row.pack(fill="x", padx=20, pady=(0, 14))
        cards_row.grid_columnconfigure((0, 1, 2), weight=1, uniform="bill_kpi")

        self.card_revenue = StatCard(
            cards_row,
            title="Today's Revenue",
            value="—",
            subtitle="Gross clinical receipts",
            icon="💵",
            accent_color=Theme.PRIMARY
        )
        self.card_revenue.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.card_bills = StatCard(
            cards_row,
            title="Bills Issued Today",
            value="—",
            subtitle="Patient checkouts",
            icon="🧾",
            accent_color=Theme.SUCCESS_TEXT
        )
        self.card_bills.grid(row=0, column=1, sticky="nsew", padx=4)

        self.card_units = StatCard(
            cards_row,
            title="Units Dispensed Today",
            value="—",
            subtitle="Physical stock depleted",
            icon="💊",
            accent_color="#3B82F6"
        )
        self.card_units.grid(row=0, column=2, sticky="nsew", padx=(8, 0))

        # 3. Filter Bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 12))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Search bills by invoice number, patient name, or phone...",
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._apply_filters)

        # 4. DataTable
        columns = [
            {"key": "invoice_number", "title": "Invoice #", "weight": 2, "sortable": True, "formatter": self._format_inv},
            {"key": "customer_name", "title": "Patient / Customer", "weight": 3, "sortable": True},
            {"key": "customer_phone", "title": "Contact", "weight": 2, "sortable": True, "formatter": lambda v: v or "—"},
            {"key": "items_count", "title": "Items", "weight": 1, "sortable": True, "formatter": lambda v: f"{v} lines"},
            {"key": "total_amount", "title": "Grand Total", "weight": 2, "sortable": True, "formatter": self._format_amount},
            {"key": "payment_method", "title": "Tender", "weight": 2, "sortable": True},
            {"key": "payment_status", "title": "Status", "weight": 1, "sortable": True, "formatter": self._format_status},
            {"key": "created_at_fmt", "title": "Date / Time", "weight": 2, "sortable": True},
        ]

        actions = [
            {"icon": "👁 Show Bill", "width": 80, "command": self._show_receipt_dialog},
        ]

        self.table = DataTable(
            self,
            columns=columns,
            data=[],
            actions=actions,
            page_size=10
        )
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def _format_inv(self, val):
        return f"📄 {val}"

    def _format_amount(self, val):
        return f"${float(val):.2f}"

    def _format_status(self, val):
        badge_variant = "success" if str(val).lower() == "paid" else "warning"
        return {"badge": str(val).upper(), "variant": badge_variant}

    def _load_data(self):
        self.lbl_count.configure(text="Refreshing transactions from PostgreSQL...")
        run_in_background(
            lambda: (
                self.api_client.list_sales(limit=100),
                self.api_client.get_today_sales_summary()
            ),
            on_success=self._on_data_loaded,
            on_error=self._on_load_error
        )

    def _on_data_loaded(self, result_tuple):
        sales_list, summary = result_tuple
        self.raw_sales = sales_list

        # Update KPI Cards
        rev = summary.get("today_revenue", 0.0)
        bills = summary.get("today_bills_count", 0)
        units = summary.get("today_units_dispensed", 0)

        self.card_revenue.set_value(f"${rev:.2f}")
        self.card_bills.set_value(f"{bills}")
        self.card_units.set_value(f"{units}")

        self._apply_filters()

    def _on_load_error(self, err_msg):
        self.lbl_count.configure(text=f"Error loading sales: {err_msg}")

    def _apply_filters(self, event=None):
        query = self.search_entry.get().strip().lower()

        filtered = []
        for s in self.raw_sales:
            inv = (s.get("invoice_number") or "").lower()
            name = (s.get("customer_name") or "").lower()
            phone = (s.get("customer_phone") or "").lower()

            if query and (query not in inv and query not in name and query not in phone):
                continue

            dt_raw = s.get("created_at", "")
            if "T" in dt_raw:
                try:
                    dt_obj = datetime.fromisoformat(dt_raw.replace("Z", "+00:00"))
                    dt_fmt = dt_obj.strftime("%d %b %Y, %I:%M %p")
                except Exception:
                    dt_fmt = dt_raw
            else:
                dt_fmt = dt_raw

            row = dict(s)
            row["items_count"] = len(s.get("items", []))
            row["created_at_fmt"] = dt_fmt
            filtered.append(row)

        self.lbl_count.configure(text=f"Showing {len(filtered)} sales records in PostgreSQL")
        self.table.set_data(filtered)

    def _show_receipt_dialog(self, sale_dict: Dict[str, Any]):
        CustomerReceiptModal(self.winfo_toplevel(), sale_dict)

    def _open_new_bill_modal(self):
        def _on_success(created_sale):
            self._load_data()
            CustomerReceiptModal(self.winfo_toplevel(), created_sale)

        NewBillModal(self.winfo_toplevel(), self.api_client, on_success=_on_success)
