import threading
from datetime import date
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge
from app.ui.components.empty_state import EmptyState


class BatchModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.on_success = on_success
        self.medicines_map = {}

        self.title("Receive Inventory Batch")
        self.geometry("500x580")
        self.resizable(False, False)
        self.grab_set()

        self._build_form()
        self._load_medicines()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=22)

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
        ).pack(anchor="w", pady=(0, 16))

        # Target Medicine
        ctk.CTkLabel(container, text="Target Medicine Product *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.med_var = ctk.StringVar(value="Loading medicines...")
        self.med_opt = ctk.CTkOptionMenu(container, variable=self.med_var, values=["Loading..."], height=38, font=accessibility_manager.get_font(13))
        self.med_opt.pack(fill="x", pady=(2, 10))

        # Batch Number
        ctk.CTkLabel(container, text="Batch / Lot Number *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_batch = ctk.CTkEntry(container, placeholder_text="e.g. LOT-2026-A1", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_batch.pack(fill="x", pady=(2, 10))

        # Expiry Date
        ctk.CTkLabel(container, text="Expiry Date * (YYYY-MM-DD)", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_exp = ctk.CTkEntry(container, placeholder_text="e.g. 2027-12-31", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_exp.pack(fill="x", pady=(2, 10))

        # Quantity
        ctk.CTkLabel(container, text="Received Quantity (Units) *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_qty = ctk.CTkEntry(container, placeholder_text="e.g. 100", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_qty.pack(fill="x", pady=(2, 10))

        # Pricing Row
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", pady=(0, 12))

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
            height=42,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._save,
            font=accessibility_manager.get_font(13, weight="bold")
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            height=42,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            command=self.destroy,
            font=accessibility_manager.get_font(13)
        ).pack(side="right", padx=(10, 0))

    def _load_medicines(self):
        def _fetch():
            try:
                meds = self.api_client.list_medicines(limit=300)
                self.after(0, self._populate_medicines, meds)
            except Exception as e:
                self.after(0, self._on_err, f"Failed loading medicines: {e}")

        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_medicines(self, medicines):
        if not medicines:
            self.med_opt.configure(values=["No medicines available - Add one first"])
            self.med_var.set("No medicines available - Add one first")
            return

        self.medicines_map = {f"{m['name']} ({m['medicine_code']})": m["id"] for m in medicines}
        names = list(self.medicines_map.keys())
        self.med_opt.configure(values=names)
        self.med_var.set(names[0])

    def _save(self):
        med_key = self.med_var.get()
        batch_no = self.entry_batch.get().strip().upper()
        exp_str = self.entry_exp.get().strip()
        qty_str = self.entry_qty.get().strip()
        cost_str = self.entry_cost.get().strip() or "0.00"
        sell_str = self.entry_sell.get().strip() or "0.00"

        if med_key not in self.medicines_map:
            self.lbl_error.configure(text="Please select a valid medicine product.")
            return

        if not batch_no or not exp_str or not qty_str:
            self.lbl_error.configure(text="Batch number, expiry date, and quantity are required.")
            return

        try:
            exp_date = date.fromisoformat(exp_str)
            if exp_date <= date.today():
                self.lbl_error.configure(text="TQM Rule: Expiry date has passed. Expired stock cannot be accepted.")
                return
        except ValueError:
            self.lbl_error.configure(text="Invalid date format. Use YYYY-MM-DD (e.g. 2027-12-31).")
            return

        try:
            qty = int(qty_str)
            if qty <= 0:
                self.lbl_error.configure(text="Quantity must be greater than zero.")
                return
        except ValueError:
            self.lbl_error.configure(text="Quantity must be a positive whole number.")
            return

        med_id = self.medicines_map[med_key]

        payload = {
            "medicine_id": med_id,
            "batch_number": batch_no,
            "expiry_date": exp_str,
            "quantity": qty,
            "cost_price": cost_str,
            "selling_price": sell_str
        }

        self.btn_save.configure(state="disabled", text="Saving...")
        self.lbl_error.configure(text="")

        def _do():
            try:
                self.api_client.create_batch(payload)
                self.after(0, self._on_done)
            except Exception as e:
                self.after(0, self._on_err, str(e))

        threading.Thread(target=_do, daemon=True).start()

    def _on_done(self):
        if self.on_success:
            self.on_success()
        self.destroy()

    def _on_err(self, err_msg):
        self.btn_save.configure(state="normal", text="Commit Batch to Stock")
        self.lbl_error.configure(text=err_msg.replace("RuntimeError: ", ""))


class InventoryView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
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
            text="📦 Inventory Lots & Expiry Control",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.status_lbl = ctk.CTkLabel(
            title_box,
            text="Loading physical lots...",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.status_lbl.pack(anchor="w")

        btn_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=95,
            height=36,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            command=self.load_batches,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ Receive Batch",
            width=150,
            height=36,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_add_modal,
            font=accessibility_manager.get_font(13, weight="bold")
        ).pack(side="left", padx=5)

        # Filter Segment Bar
        filter_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        self.filter_var = ctk.StringVar(value="All Active Batches")
        self.seg_btn = ctk.CTkSegmentedButton(
            filter_card,
            values=["All Active Batches", "Expiring Soon (<30 Days)", "Expired Batches"],
            variable=self.filter_var,
            command=lambda v: self.load_batches(),
            font=accessibility_manager.get_font(12, weight="bold")
        )
        self.seg_btn.pack(side="left", padx=12, pady=10)

        # Main Table Card
        self.table_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        self.table_card.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        # Header Row
        self.hdr = ctk.CTkFrame(self.table_card, fg_color=Theme.BG_MUTED, height=38, corner_radius=8)
        self.hdr.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(self.hdr, text="BATCH # / LOT", width=130, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="MEDICINE PRODUCT", width=220, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="EXPIRY DATE", width=120, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="QUANTITY", width=90, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="RETAIL PRICE", width=90, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="EXPIRY COMPLIANCE", width=140, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)

        # Scrollable Rows
        self.table_scroll = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _open_add_modal(self):
        BatchModal(self, self.api_client, on_success=self.load_batches)

    def load_batches(self):
        filter_mode = self.filter_var.get()
        self.status_lbl.configure(text=f"⏳ Fetching {filter_mode.lower()}...")

        def _fetch():
            try:
                if filter_mode == "Expiring Soon (<30 Days)":
                    batches = self.api_client.list_expiring_soon(days=30)
                elif filter_mode == "Expired Batches":
                    batches = [b for b in self.api_client.list_batches() if b.get("is_expired")]
                else:
                    batches = self.api_client.list_batches()
                self.after(0, self._render_batches, batches)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_batches(self, batches):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        self.status_lbl.configure(text=f"Total: {len(batches)} batches in physical inventory")

        if not batches:
            EmptyState(
                self.table_scroll,
                icon="📦",
                title="No Batches Found",
                description="No physical inventory lots match your selected filter.",
                action_text="➕ Receive New Batch",
                action_command=self._open_add_modal
            ).pack(fill="both", expand=True, pady=30)
            return

        for idx, b in enumerate(batches):
            row_bg = "transparent" if idx % 2 == 0 else Theme.BG_MUTED
            row = ctk.CTkFrame(self.table_scroll, fg_color=row_bg, corner_radius=6, height=44)
            row.pack(fill="x", pady=2)

            # Batch #
            code_box = ctk.CTkFrame(row, fg_color="transparent", width=130)
            code_box.pack(side="left", padx=8)
            StatusBadge(code_box, text=b["batch_number"], variant="info").pack(anchor="w")

            # Medicine Name
            ctk.CTkLabel(
                row,
                text=b.get("medicine_name") or "—",
                width=220,
                anchor="w",
                font=accessibility_manager.get_font(13, weight="bold"),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=8)

            # Expiry Date
            ctk.CTkLabel(
                row,
                text=str(b["expiry_date"]),
                width=120,
                anchor="center",
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=8)

            # Stock Qty
            ctk.CTkLabel(
                row,
                text=f"{b['quantity']} Units",
                width=90,
                anchor="center",
                font=accessibility_manager.get_font(12, weight="bold"),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=8)

            # Price
            ctk.CTkLabel(
                row,
                text=f"${float(b.get('selling_price', 0)):.2f}",
                width=90,
                anchor="center",
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MUTED
            ).pack(side="left", padx=8)

            # Expiry Compliance Badge
            days = b.get("days_until_expiry", 0)
            badge_box = ctk.CTkFrame(row, fg_color="transparent", width=140)
            badge_box.pack(side="left", padx=8)

            if b.get("is_expired") or days < 0:
                StatusBadge(badge_box, text="EXPIRED LOT", variant="danger").pack(expand=True)
            elif days <= 30:
                StatusBadge(badge_box, text=f"Exp in {days}d", variant="warning").pack(expand=True)
            else:
                StatusBadge(badge_box, text=f"Valid ({days}d)", variant="success").pack(expand=True)

    def _render_error(self, err_msg):
        self.status_lbl.configure(text=f"Error: {err_msg}", text_color=Theme.DANGER_TEXT)
