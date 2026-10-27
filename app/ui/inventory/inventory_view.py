"""
Batch Inventory Management View.
Integrated with responsive DataTable, segmented filters, pagination, DetailModal, and BatchModal with TQM date validation.
"""
import threading
from datetime import date
from typing import Optional, Dict, Any, List
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.badge import StatusBadge
from app.ui.components.dialogs import DetailModal
from app.ui.components.data_table import DataTable


class BatchModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.on_success = on_success
        self.medicines_map = {}

        self.title("Receive Inventory Batch")
        self.geometry("500x600")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()
        self._load_medicines()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=20)

        ctk.CTkLabel(
            container,
            text="Receive Inventory Batch",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            container,
            text="TQM Control: Verifies expiry dates and records physical lots into stock",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Target Medicine
        ctk.CTkLabel(container, text="Target Medicine Product *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.med_var = ctk.StringVar(value="Loading medicines...")
        self.med_opt = ctk.CTkOptionMenu(container, variable=self.med_var, values=["Loading..."], height=38, font=accessibility_manager.get_font(13))
        self.med_opt.pack(fill="x", pady=(2, 8))

        # Batch Number
        ctk.CTkLabel(container, text="Batch / Lot Number *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_batch = ctk.CTkEntry(container, placeholder_text="e.g. LOT-2026-A1", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_batch.pack(fill="x", pady=(2, 8))

        # Expiry Date
        ctk.CTkLabel(container, text="Expiry Date * (YYYY-MM-DD)", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_exp = ctk.CTkEntry(container, placeholder_text="e.g. 2027-12-31", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_exp.pack(fill="x", pady=(2, 8))

        # Quantity
        ctk.CTkLabel(container, text="Received Quantity (Units) *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_qty = ctk.CTkEntry(container, placeholder_text="e.g. 100", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_qty.pack(fill="x", pady=(2, 8))

        # Pricing Row
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        col_cost = ctk.CTkFrame(row, fg_color="transparent")
        col_cost.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkLabel(col_cost, text="Cost Price ($)", font=accessibility_manager.get_font(13), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_cost = ctk.CTkEntry(col_cost, placeholder_text="0.00", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_cost.pack(fill="x", pady=(2, 0))

        col_sell = ctk.CTkFrame(row, fg_color="transparent")
        col_sell.pack(side="right", expand=True, fill="x", padx=(6, 0))
        ctk.CTkLabel(col_sell, text="Retail Selling Price ($)", font=accessibility_manager.get_font(13), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_sell = ctk.CTkEntry(col_sell, placeholder_text="0.00", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_sell.pack(fill="x", pady=(2, 0))

        self.lbl_error = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(12))
        self.lbl_error.pack(anchor="w", pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="Commit Batch to Stock",
            height=40,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._save,
            font=accessibility_manager.get_font(13, weight="bold")
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel (Esc)",
            height=40,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            command=self.destroy,
            font=accessibility_manager.get_font(13)
        ).pack(side="right", padx=(10, 0))

    def _load_medicines(self):
        run_in_background(
            lambda: self.api_client.list_medicines(is_active=True),
            on_success=self._populate_medicines,
            on_error=lambda e: self._on_err(f"Failed loading medicines: {e}")
        )

    def _populate_medicines(self, medicines):
        if not medicines:
            self.med_opt.configure(values=["No active medicines in formulary"])
            self.med_var.set("No active medicines in formulary")
            return

        self.medicines_map = {f"{m['name']} ({m['medicine_code']})": m["id"] for m in medicines}
        med_names = list(self.medicines_map.keys())
        self.med_opt.configure(values=med_names)
        self.med_var.set(med_names[0])

    def _save(self):
        med_key = self.med_var.get()
        batch_no = self.entry_batch.get().strip().upper()
        exp_str = self.entry_exp.get().strip()
        qty_str = self.entry_qty.get().strip()
        cost_str = self.entry_cost.get().strip() or "0.00"
        sell_str = self.entry_sell.get().strip() or "0.00"

        if med_key not in self.medicines_map:
            self.lbl_error.configure(text="Please select an active medicine.")
            return

        if not batch_no or not exp_str or not qty_str:
            self.lbl_error.configure(text="Batch number, expiry date, and quantity are required.")
            return

        try:
            exp_date = date.fromisoformat(exp_str)
            if exp_date <= date.today():
                self.lbl_error.configure(text="TQM Poka-Yoke: Expiry date must be strictly in the future.")
                return
        except ValueError:
            self.lbl_error.configure(text="Invalid expiry date format. Use YYYY-MM-DD.")
            return

        try:
            qty = int(qty_str)
            if qty <= 0:
                self.lbl_error.configure(text="Quantity must be greater than zero.")
                return
        except ValueError:
            self.lbl_error.configure(text="Quantity must be a valid whole number.")
            return

        payload = {
            "medicine_id": self.medicines_map[med_key],
            "batch_number": batch_no,
            "expiry_date": exp_str,
            "quantity": qty,
            "cost_price": cost_str,
            "selling_price": sell_str
        }

        self.btn_save.configure(state="disabled", text="Committing Batch...")
        self.lbl_error.configure(text="")

        run_in_background(
            lambda: self.api_client.create_batch(payload),
            on_success=lambda _: self._on_done(),
            on_error=self._on_err
        )

    def _on_done(self):
        if self.on_success:
            self.on_success()
        self.destroy()

    def _on_err(self, msg: str):
        self.btn_save.configure(state="normal", text="Commit Batch to Stock")
        clean_msg = msg.replace("RuntimeError: ", "")
        self.lbl_error.configure(text=clean_msg)


class InventoryView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.raw_batches: List[Dict[str, Any]] = []
        self.current_filter = "all"

        self._build_ui()
        self.load_batches()

    def _build_ui(self):
        # Action Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📦 Pharmaceutical Batch Inventory",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading batch inventory from PostgreSQL...",
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
            command=self.load_batches,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ Receive Batch",
            width=140,
            height=36,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_receive_modal,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        # Filters Row
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Filter by batch number or medicine name...",
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._apply_filters)

        # Segmented Filter Buttons
        self.filter_buttons = {}
        filters = [
            ("all", "All Batches"),
            ("active", "Active Lots"),
            ("expiring", "Expiring Soon (<30d)"),
            ("expired", "Expired Lots")
        ]
        seg_frame = ctk.CTkFrame(filter_bar, fg_color=Theme.BG_MUTED, corner_radius=8, height=36)
        seg_frame.pack(side="left")

        for key, label in filters:
            btn = ctk.CTkButton(
                seg_frame,
                text=label,
                height=30,
                corner_radius=6,
                fg_color=Theme.PRIMARY if key == "all" else "transparent",
                hover_color=Theme.PRIMARY_HOVER,
                text_color="#FFFFFF" if key == "all" else Theme.TEXT_MUTED,
                font=accessibility_manager.get_font(11, weight="bold"),
                command=lambda k=key: self._set_filter(k)
            )
            btn.pack(side="left", padx=2, pady=3)
            self.filter_buttons[key] = btn

        # DataTable
        columns = [
            {"key": "batch_number", "title": "Batch / Lot #", "weight": 2, "sortable": True, "formatter": self._format_batch_no},
            {"key": "medicine_name", "title": "Target Medicine", "weight": 3, "sortable": True},
            {"key": "quantity", "title": "Units In-Stock", "weight": 1, "align": "center", "sortable": True, "formatter": self._format_units},
            {"key": "cost_price", "title": "Cost", "weight": 1, "formatter": lambda p, v, r: ctk.CTkLabel(p, text=f"${float(v or 0):.2f}", font=accessibility_manager.get_font(12), text_color=Theme.TEXT_MUTED)},
            {"key": "selling_price", "title": "Retail", "weight": 1, "formatter": lambda p, v, r: ctk.CTkLabel(p, text=f"${float(v or 0):.2f}", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN)},
            {"key": "expiry_date", "title": "Expiry Date", "weight": 2, "sortable": True, "formatter": self._format_expiry_date},
            {"key": "compliance", "title": "TQM Compliance", "weight": 2, "formatter": self._format_compliance}
        ]

        actions = [
            {"icon": "👁 Inspect", "width": 74, "command": self._view_details}
        ]

        self.table = DataTable(
            self,
            columns=columns,
            actions=actions,
            page_size=10,
            empty_title="No Inventory Batches Found",
            empty_desc="Click '➕ Receive Batch' above to record inbound pharmaceutical shipments into stock."
        )
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _format_batch_no(self, parent, val, row):
        return ctk.CTkLabel(
            parent,
            text=str(val or "—"),
            font=accessibility_manager.get_font(12, weight="bold", family="Consolas"),
            text_color=Theme.PRIMARY,
            anchor="w"
        )

    def _format_units(self, parent, val, row):
        qty = val if val is not None else 0
        return ctk.CTkLabel(
            parent,
            text=f"{qty} Units",
            font=accessibility_manager.get_font(12, weight="bold"),
            text_color=Theme.TEXT_MAIN,
            anchor="center"
        )

    def _format_expiry_date(self, parent, val, row):
        days = row.get("days_until_expiry", 0)
        tag = f" ({days}d remaining)" if days > 0 else " (EXPIRED)"
        return ctk.CTkLabel(
            parent,
            text=f"{val}{tag}",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MAIN,
            anchor="w"
        )

    def _format_compliance(self, parent, val, row):
        is_exp = row.get("is_expired", False)
        days = row.get("days_until_expiry", 0)

        if is_exp or days <= 0:
            return StatusBadge(parent, text="EXPIRED (Blocked)", variant="danger")
        elif days <= 30:
            return StatusBadge(parent, text=f"Exp in {days}d", variant="warning")
        else:
            return StatusBadge(parent, text="Valid Lot", variant="success")

    def _view_details(self, batch):
        details = {
            "Batch / Lot #": batch.get("batch_number"),
            "Medicine Name": batch.get("medicine_name") or "Unspecified",
            "Medicine SKU": batch.get("medicine_code") or "—",
            "Physical Quantity": f"{batch.get('quantity', 0)} Units",
            "Cost Price": f"${float(batch.get('cost_price', 0)):.2f}",
            "Selling Retail Price": f"${float(batch.get('selling_price', 0)):.2f}",
            "Expiry Date": str(batch.get("expiry_date")),
            "Days Until Expiry": f"{batch.get('days_until_expiry', 0)} Days",
            "TQM Status": "EXPIRED - Quarantined from Sales" if batch.get("is_expired") else "Active & Valid Lot",
            "Supplier": batch.get("supplier_name") or "Direct Inbound Shipment",
            "Record ID": batch.get("id")
        }
        DetailModal(self.winfo_toplevel(), title=f"Lot {batch.get('batch_number')}", subtitle="Batch Quality & Audit Record", data_dict=details)

    def _open_receive_modal(self):
        BatchModal(self.winfo_toplevel(), self.api_client, on_success=self.load_batches)

    def _set_filter(self, key: str):
        self.current_filter = key
        for k, btn in self.filter_buttons.items():
            if k == key:
                btn.configure(fg_color=Theme.PRIMARY, text_color="#FFFFFF")
            else:
                btn.configure(fg_color="transparent", text_color=Theme.TEXT_MUTED)
        self._apply_filters()

    def _apply_filters(self, event=None):
        q = self.search_entry.get().strip().lower()

        def match(b):
            # 1. Text filter
            if q:
                b_match = q in b.get("batch_number", "").lower()
                m_match = bool(b.get("medicine_name") and q in b["medicine_name"].lower())
                if not (b_match or m_match):
                    return False

            # 2. Segment filter
            is_exp = b.get("is_expired", False)
            days = b.get("days_until_expiry", 0)

            if self.current_filter == "active" and (is_exp or days <= 0):
                return False
            if self.current_filter == "expiring" and not (0 < days <= 30 and not is_exp):
                return False
            if self.current_filter == "expired" and not (is_exp or days <= 0):
                return False

            return True

        self.table.filter(match)

    def load_batches(self):
        self.lbl_count.configure(text="⏳ Querying database via FastAPI...", text_color=Theme.TEXT_MUTED)
        run_in_background(
            lambda: self.api_client.list_batches(),
            on_success=self._render_batches,
            on_error=lambda e: self.lbl_count.configure(text=f"API Error: {e}", text_color=Theme.DANGER_TEXT)
        )

    def _render_batches(self, batches):
        self.raw_batches = batches or []
        tot_units = sum(b.get("quantity", 0) for b in self.raw_batches)
        self.lbl_count.configure(
            text=f"Total: {len(self.raw_batches)} active batches ({tot_units} physical units) in PostgreSQL",
            text_color=Theme.TEXT_MUTED
        )
        self.table.set_data(self.raw_batches)
