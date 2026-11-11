"""
Inbound Purchases & Consignment Receiving View.
Integrated with supplier selection, batch receiving, stock updates, and accessibility standards.
"""
from typing import Optional, Dict, Any, List
from datetime import date
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.badge import StatusBadge
from app.ui.components.data_table import DataTable


class NewPurchaseModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.on_success = on_success

        self.title("Receive Inbound Wholesale Consignment")
        self.geometry("640x620")
        self.resizable(False, False)
        self.grab_set()

        self.suppliers = []
        self.medicines = []
        self.items = []

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()
        self._load_meta()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            container,
            text="Inbound Purchase Consignment",
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text="Records procurement invoice and creates physical batch inventory",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 12))

        # Row: Supplier & PO Number
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        c_sup = ctk.CTkFrame(row1, fg_color="transparent")
        c_sup.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(c_sup, text="Distributor / Supplier *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.sup_var = ctk.StringVar(value="Loading suppliers...")
        self.sup_opt = ctk.CTkOptionMenu(c_sup, variable=self.sup_var, values=["Loading..."], height=36)
        self.sup_opt.pack(fill="x", pady=(2, 0))

        c_inv = ctk.CTkFrame(row1, fg_color="transparent")
        c_inv.pack(side="right", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(c_inv, text="Vendor Invoice # (Optional)", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_inv = ctk.CTkEntry(c_inv, placeholder_text="e.g. APEX-INV-9921", height=36)
        self.entry_inv.pack(fill="x", pady=(2, 0))

        # Medicine & Batch Selection Box
        box = ctk.CTkFrame(container, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER)
        box.pack(fill="x", pady=(4, 10), padx=0)

        inner = ctk.CTkFrame(box, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        ctk.CTkLabel(inner, text="Select Medicine Catalog Item *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.med_var = ctk.StringVar(value="Loading medicines...")
        self.med_opt = ctk.CTkOptionMenu(inner, variable=self.med_var, values=["Loading..."], height=34)
        self.med_opt.pack(fill="x", pady=(2, 8))

        # Batch, Qty, Cost, Selling, Expiry
        b_row = ctk.CTkFrame(inner, fg_color="transparent")
        b_row.pack(fill="x", pady=(0, 8))

        c_bnum = ctk.CTkFrame(b_row, fg_color="transparent")
        c_bnum.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ctk.CTkLabel(c_bnum, text="Batch Lot # *", font=accessibility_manager.get_font(11)).pack(anchor="w")
        self.entry_batch = ctk.CTkEntry(c_bnum, placeholder_text="e.g. LOT-2026-X", height=32)
        self.entry_batch.pack(fill="x")

        c_qty = ctk.CTkFrame(b_row, fg_color="transparent")
        c_qty.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(c_qty, text="Quantity *", font=accessibility_manager.get_font(11)).pack(anchor="w")
        self.entry_qty = ctk.CTkEntry(c_qty, placeholder_text="e.g. 100", height=32)
        self.entry_qty.pack(fill="x")

        c_cost = ctk.CTkFrame(b_row, fg_color="transparent")
        c_cost.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(c_cost, text="Cost Price (₹) *", font=accessibility_manager.get_font(11)).pack(anchor="w")
        self.entry_cost = ctk.CTkEntry(c_cost, placeholder_text="e.g. 15.50", height=32)
        self.entry_cost.pack(fill="x")

        c_sell = ctk.CTkFrame(b_row, fg_color="transparent")
        c_sell.pack(side="left", fill="x", expand=True, padx=(4, 0))
        ctk.CTkLabel(c_sell, text="Selling Price (₹)", font=accessibility_manager.get_font(11)).pack(anchor="w")
        self.entry_sell = ctk.CTkEntry(c_sell, placeholder_text="e.g. 25.00", height=32)
        self.entry_sell.pack(fill="x")

        # Expiry & Add button
        e_row = ctk.CTkFrame(inner, fg_color="transparent")
        e_row.pack(fill="x")

        c_exp = ctk.CTkFrame(e_row, fg_color="transparent")
        c_exp.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkLabel(c_exp, text="Expiry Date (YYYY-MM-DD)", font=accessibility_manager.get_font(11)).pack(anchor="w")
        self.entry_exp = ctk.CTkEntry(c_exp, placeholder_text="e.g. 2027-12-31", height=32)
        self.entry_exp.pack(fill="x")

        ctk.CTkButton(
            e_row,
            text="➕ Add Item to PO",
            height=32,
            fg_color=Theme.SECONDARY,
            text_color=Theme.SECONDARY_TEXT,
            command=self._add_item
        ).pack(side="right", pady=(18, 0))

        # Items List Table Preview
        self.lbl_items_summary = ctk.CTkLabel(
            container,
            text="Items to Receive: 0 | Total: ₹0.00",
            font=accessibility_manager.get_font(12, weight="bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_items_summary.pack(anchor="w", pady=(4, 4))

        self.box_items = ctk.CTkTextbox(container, height=120, font=accessibility_manager.get_font(11))
        self.box_items.pack(fill="x", pady=(0, 10))
        self.box_items.insert("1.0", "No line items added yet.\n")
        self.box_items.configure(state="disabled")

        self.lbl_err = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(11))
        self.lbl_err.pack(anchor="w", pady=(0, 6))

        # Final Action Buttons
        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_submit = ctk.CTkButton(
            btn_box,
            text="Receive & Commit Inbound Stock",
            height=40,
            fg_color=Theme.PRIMARY,
            command=self._submit
        )
        self.btn_submit.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            height=40,
            fg_color=Theme.SECONDARY,
            text_color=Theme.SECONDARY_TEXT,
            command=self.destroy
        ).pack(side="right", padx=(6, 0))

    def _load_meta(self):
        def _fetch():
            sups = self.api_client.list_suppliers()
            meds = self.api_client.list_medicines(limit=500)
            return sups, meds

        def _on_done(result):
            self.suppliers, self.medicines = result
            if self.suppliers:
                sup_names = [s["name"] for s in self.suppliers]
                self.sup_opt.configure(values=sup_names)
                self.sup_var.set(sup_names[0])
            else:
                self.sup_opt.configure(values=["No suppliers found - Add supplier first"])
                self.sup_var.set("No suppliers found - Add supplier first")

            if self.medicines:
                med_names = [f"{m['name']} ({m.get('medicine_code', '')})" for m in self.medicines]
                self.med_opt.configure(values=med_names)
                self.med_var.set(med_names[0])
            else:
                self.med_opt.configure(values=["No medicines found"])
                self.med_var.set("No medicines found")

        run_in_background(_fetch, on_success=_on_done)

    def _add_item(self):
        sel_med_str = self.med_var.get()
        if not self.medicines or "No medicines" in sel_med_str:
            self.lbl_err.configure(text="Please add medicines to catalog first.")
            return

        med_idx = self.med_opt.cget("values").index(sel_med_str)
        med = self.medicines[med_idx]

        b_num = self.entry_batch.get().strip()
        qty_str = self.entry_qty.get().strip()
        cost_str = self.entry_cost.get().strip()
        sell_str = self.entry_sell.get().strip()
        exp_str = self.entry_exp.get().strip()

        if not b_num:
            self.lbl_err.configure(text="Batch lot number is required.")
            return
        if not qty_str.isdigit() or int(qty_str) <= 0:
            self.lbl_err.configure(text="Quantity must be a positive integer.")
            return
        try:
            cost = float(cost_str)
            if cost < 0:
                raise ValueError()
        except Exception:
            self.lbl_err.configure(text="Invalid unit cost price.")
            return

        sell = float(sell_str) if sell_str else round(cost * 1.30, 2)

        self.items.append({
            "medicine_id": med["id"],
            "medicine_name": med["name"],
            "batch_number": b_num,
            "quantity": int(qty_str),
            "unit_cost": cost,
            "selling_price": sell,
            "expiry_date": exp_str or None
        })

        # Clear inputs
        self.entry_batch.delete(0, "end")
        self.entry_qty.delete(0, "end")
        self.entry_cost.delete(0, "end")
        self.entry_sell.delete(0, "end")
        self.entry_exp.delete(0, "end")
        self.lbl_err.configure(text="")

        self._refresh_items_preview()

    def _refresh_items_preview(self):
        total = sum(i["quantity"] * i["unit_cost"] for i in self.items)
        self.lbl_items_summary.configure(text=f"Items to Receive: {len(self.items)} | Total Amount: ₹{total:.2f}")

        self.box_items.configure(state="normal")
        self.box_items.delete("1.0", "end")
        for idx, item in enumerate(self.items, 1):
            sub = item["quantity"] * item["unit_cost"]
            self.box_items.insert(
                "end",
                f"{idx}. {item['medicine_name']} | Lot: {item['batch_number']} | Qty: {item['quantity']} @ ₹{item['unit_cost']:.2f} = ₹{sub:.2f}\n"
            )
        self.box_items.configure(state="disabled")

    def _submit(self):
        if not self.items:
            self.lbl_err.configure(text="Please add at least one line item to consignment.")
            return

        sel_sup_str = self.sup_var.get()
        if not self.suppliers or "No suppliers" in sel_sup_str:
            self.lbl_err.configure(text="Valid supplier required.")
            return

        sup_idx = self.sup_opt.cget("values").index(sel_sup_str)
        sup = self.suppliers[sup_idx]

        payload = {
            "supplier_id": sup["id"],
            "invoice_number": self.entry_inv.get().strip() or None,
            "items": self.items
        }

        self.btn_submit.configure(state="disabled", text="Receiving & Committing Stock...")

        def _do():
            return self.api_client.create_purchase(payload)

        run_in_background(
            _do,
            on_success=lambda _: self._on_done(),
            on_error=lambda err: self._on_err(err)
        )

    def _on_done(self):
        if self.on_success:
            self.on_success()
        self.destroy()

    def _on_err(self, err):
        self.btn_submit.configure(state="normal", text="Receive & Commit Inbound Stock")
        self.lbl_err.configure(text=str(err).replace("RuntimeError: ", ""))


class PurchaseView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.purchases_list = []

        self._build_ui()
        self.load_purchases()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🛒 Inbound Purchases & Consignments",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading purchases...",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_count.pack(anchor="w")

        btn_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=90,
            height=36,
            fg_color=Theme.SECONDARY,
            text_color=Theme.SECONDARY_TEXT,
            command=self.load_purchases
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ Receive Consignment",
            width=170,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._open_receive_modal
        ).pack(side="left", padx=5)

        # Table
        self.columns = [
            {"key": "invoice", "title": "Invoice #", "width": 160, "anchor": "w"},
            {"key": "supplier", "title": "Supplier / Distributor", "width": 240, "anchor": "w"},
            {"key": "date", "title": "Received Date", "width": 150, "anchor": "w"},
            {"key": "items", "title": "Items", "width": 90, "anchor": "center"},
            {"key": "total", "title": "Total Amount", "width": 140, "anchor": "e"},
            {"key": "status", "title": "Status", "width": 110, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=self.columns, rows_per_page=12)
        self.table.pack(fill="both", expand=True, padx=20, pady=(10, 15))

    def load_purchases(self):
        self.lbl_count.configure(text="Fetching purchase orders...")
        run_in_background(
            lambda: self.api_client.list_purchases(),
            on_success=self._on_loaded,
            on_error=lambda err: self.lbl_count.configure(text=f"Error: {err}")
        )

    def _on_loaded(self, purchases):
        self.purchases_list = purchases or []
        self.lbl_count.configure(text=f"Total: {len(self.purchases_list)} recorded consignments")
        rows = []
        for p in self.purchases_list:
            rows.append({
                "invoice": p.get("invoice_number", ""),
                "supplier": p.get("supplier_name", "—"),
                "date": p.get("purchase_date", ""),
                "items": str(p.get("items_count", 0)),
                "total": f"₹{float(p.get('total_amount', 0)):.2f}",
                "status": "RECEIVED",
                "_raw": p
            })
        self.table.set_data(rows)

    def _open_receive_modal(self):
        NewPurchaseModal(self.winfo_toplevel(), self.api_client, on_success=self.load_purchases)
