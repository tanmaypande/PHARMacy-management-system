import threading
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge
from app.ui.components.empty_state import EmptyState
from app.ui.components.dialogs import ConfirmDialog


class MedicineModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, medicine=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.medicine = medicine
        self.on_success = on_success
        self.categories_map = {}

        self.title("Edit Medicine" if medicine else "Register New Medicine")
        self.geometry("540x640")
        self.resizable(False, False)
        self.grab_set()

        self._build_form()
        self._load_categories()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=22)

        title_text = "Edit Pharmaceutical Product" if self.medicine else "Register New Medicine Catalog Item"
        ctk.CTkLabel(
            container,
            text=title_text,
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            container,
            text="Master item details (inventory batches & expiry dates are received separately)",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Medicine Code
        ctk.CTkLabel(container, text="Medicine Code / SKU *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_code = ctk.CTkEntry(container, placeholder_text="e.g. MED-PARA-500", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_code.pack(fill="x", pady=(2, 10))
        if self.medicine:
            self.entry_code.insert(0, self.medicine.get("medicine_code", ""))

        # Brand Name
        ctk.CTkLabel(container, text="Trade / Brand Name *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(container, placeholder_text="e.g. Paracetamol Extra 500mg", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_name.pack(fill="x", pady=(2, 10))
        if self.medicine:
            self.entry_name.insert(0, self.medicine.get("name", ""))

        # Generic Name
        ctk.CTkLabel(container, text="Generic Chemical Compound", font=accessibility_manager.get_font(13), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_generic = ctk.CTkEntry(container, placeholder_text="e.g. Acetaminophen", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_generic.pack(fill="x", pady=(2, 10))
        if self.medicine and self.medicine.get("generic_name"):
            self.entry_generic.insert(0, self.medicine.get("generic_name", ""))

        # Category Dropdown
        ctk.CTkLabel(container, text="Therapeutic Category *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.category_var = ctk.StringVar(value="Loading categories...")
        self.category_opt = ctk.CTkOptionMenu(container, variable=self.category_var, values=["Loading..."], height=38, font=accessibility_manager.get_font(13))
        self.category_opt.pack(fill="x", pady=(2, 10))

        # 2 Columns for Manufacturer & Unit
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        col_mfg = ctk.CTkFrame(row1, fg_color="transparent")
        col_mfg.pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkLabel(col_mfg, text="Manufacturer", font=accessibility_manager.get_font(13), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_mfg = ctk.CTkEntry(col_mfg, placeholder_text="e.g. GSK, Pfizer", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_mfg.pack(fill="x", pady=(2, 0))
        if self.medicine and self.medicine.get("manufacturer"):
            self.entry_mfg.insert(0, self.medicine.get("manufacturer", ""))

        col_unit = ctk.CTkFrame(row1, fg_color="transparent")
        col_unit.pack(side="right", expand=True, fill="x", padx=(6, 0))
        ctk.CTkLabel(col_unit, text="Unit of Measure", font=accessibility_manager.get_font(13), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.unit_var = ctk.StringVar(value=self.medicine.get("unit_of_measurement", "Tablets") if self.medicine else "Tablets")
        self.unit_opt = ctk.CTkOptionMenu(
            col_unit,
            variable=self.unit_var,
            values=["Tablets", "Capsules", "Syrup (Bottle)", "Strip", "Vial", "Ointment (Tube)", "Drops", "Inhaler"],
            height=38,
            font=accessibility_manager.get_font(13)
        )
        self.unit_opt.pack(fill="x", pady=(2, 0))

        # Checkboxes row
        checks_row = ctk.CTkFrame(container, fg_color="transparent")
        checks_row.pack(fill="x", pady=(6, 12))

        self.rx_var = ctk.BooleanVar(value=self.medicine.get("prescription_required", False) if self.medicine else False)
        ctk.CTkCheckBox(checks_row, text="Prescription Required (Rx Only)", variable=self.rx_var, font=accessibility_manager.get_font(13)).pack(side="left")

        self.active_var = ctk.BooleanVar(value=self.medicine.get("is_active", True) if self.medicine else True)
        ctk.CTkCheckBox(checks_row, text="Active in Catalog", variable=self.active_var, font=accessibility_manager.get_font(13)).pack(side="right")

        self.lbl_error = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(12))
        self.lbl_error.pack(anchor="w", pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="Save Product",
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

    def _load_categories(self):
        def _fetch():
            try:
                cats = self.api_client.list_categories()
                self.after(0, self._populate_categories, cats)
            except Exception as e:
                self.after(0, self._on_err, f"Failed loading categories: {e}")

        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_categories(self, categories):
        if not categories:
            self.category_opt.configure(values=["No categories found - Add one first"])
            self.category_var.set("No categories found - Add one first")
            return

        self.categories_map = {c["name"]: c["id"] for c in categories}
        cat_names = list(self.categories_map.keys())
        self.category_opt.configure(values=cat_names)

        if self.medicine and self.medicine.get("category_name") in self.categories_map:
            self.category_var.set(self.medicine["category_name"])
        else:
            self.category_var.set(cat_names[0])

    def _save(self):
        code = self.entry_code.get().strip().upper()
        name = self.entry_name.get().strip()
        generic = self.entry_generic.get().strip() or None
        cat_name = self.category_var.get()
        mfg = self.entry_mfg.get().strip() or None
        unit = self.unit_var.get()
        rx = self.rx_var.get()
        active = self.active_var.get()

        if not code or not name:
            self.lbl_error.configure(text="Medicine Code and Brand Name are required.")
            return

        if cat_name not in self.categories_map:
            self.lbl_error.configure(text="Please select a valid Category.")
            return

        payload = {
            "medicine_code": code,
            "name": name,
            "generic_name": generic,
            "category_id": self.categories_map[cat_name],
            "manufacturer": mfg,
            "unit_of_measurement": unit,
            "reorder_level": 10,
            "prescription_required": rx,
            "is_active": active
        }

        self.btn_save.configure(state="disabled", text="Saving...")
        self.lbl_error.configure(text="")

        def _do():
            try:
                if self.medicine:
                    self.api_client.update_medicine(self.medicine["id"], payload)
                else:
                    self.api_client.create_medicine(payload)
                self.after(0, self._on_done)
            except Exception as e:
                self.after(0, self._on_err, str(e))

        threading.Thread(target=_do, daemon=True).start()

    def _on_done(self):
        if self.on_success:
            self.on_success()
        self.destroy()

    def _on_err(self, err_msg):
        self.btn_save.configure(state="normal", text="Save Product")
        self.lbl_error.configure(text=err_msg.replace("RuntimeError: ", ""))


class MedicineView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.categories_map = {}
        self._build_ui()
        self.load_medicines()

    def _build_ui(self):
        # Action Toolbar Row
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="💊 Medicine Catalog & Formulary",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.status_lbl = ctk.CTkLabel(
            title_box,
            text="Loading medicines catalog...",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.status_lbl.pack(anchor="w")

        ctk.CTkButton(
            toolbar,
            text="➕ Register Medicine",
            width=160,
            height=36,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_add_modal,
            font=accessibility_manager.get_font(13, weight="bold")
        ).pack(side="right")

        # Filters Bar (Card Container)
        filter_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        # Search box
        self.entry_search = ctk.CTkEntry(
            filter_card,
            placeholder_text="🔍 Search brand, chemical generic, or SKU code...",
            width=320,
            height=36,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(13)
        )
        self.entry_search.pack(side="left", padx=12, pady=10)
        self.entry_search.bind("<Return>", lambda e: self.load_medicines())

        ctk.CTkButton(
            filter_card,
            text="Filter",
            width=75,
            height=36,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            command=self.load_medicines,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=(0, 10))

        # Category Filter
        self.cat_filter_var = ctk.StringVar(value="All Categories")
        self.cat_filter_opt = ctk.CTkOptionMenu(
            filter_card,
            variable=self.cat_filter_var,
            values=["All Categories"],
            command=lambda v: self.load_medicines(),
            height=36,
            font=accessibility_manager.get_font(12)
        )
        self.cat_filter_opt.pack(side="left", padx=5)

        ctk.CTkButton(
            filter_card,
            text="Clear",
            width=65,
            height=36,
            fg_color="transparent",
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MUTED,
            command=self._reset_filters,
            font=accessibility_manager.get_font(12)
        ).pack(side="right", padx=12)

        # Main Table Card
        self.table_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        self.table_card.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        # Header Row
        self.hdr = ctk.CTkFrame(self.table_card, fg_color=Theme.BG_MUTED, height=38, corner_radius=8)
        self.hdr.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(self.hdr, text="SKU / CODE", width=120, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="TRADE BRAND NAME", width=190, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="GENERIC COMPOUND", width=150, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="CATEGORY", width=120, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="AVAILABLE STOCK", width=110, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="STATUS", width=80, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(self.hdr, text="ACTIONS", width=110, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)

        # Scrollable Rows Container
        self.table_scroll = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _reset_filters(self):
        self.entry_search.delete(0, "end")
        self.cat_filter_var.set("All Categories")
        self.load_medicines()

    def _open_add_modal(self):
        MedicineModal(self, self.api_client, on_success=self.load_medicines)

    def _open_edit_modal(self, medicine):
        MedicineModal(self, self.api_client, medicine=medicine, on_success=self.load_medicines)

    def load_medicines(self):
        search_query = self.entry_search.get().strip() or None
        cat_selected = self.cat_filter_var.get()
        cat_id = self.categories_map.get(cat_selected) if cat_selected != "All Categories" else None

        self.status_lbl.configure(text="⏳ Querying medicine catalog...")

        def _fetch():
            try:
                cats = self.api_client.list_categories()
                meds = self.api_client.list_medicines(search=search_query, category_id=cat_id)
                self.after(0, self._render_results, meds, cats)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_results(self, medicines, categories):
        self.categories_map = {c["name"]: c["id"] for c in categories}
        dropdown_vals = ["All Categories"] + list(self.categories_map.keys())
        self.cat_filter_opt.configure(values=dropdown_vals)

        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        self.status_lbl.configure(text=f"Total: {len(medicines)} formulary products matching search")

        if not medicines:
            EmptyState(
                self.table_scroll,
                icon="💊",
                title="No Medicines Found",
                description="No products match your current search filters. Register new items or adjust criteria.",
                action_text="➕ Register Medicine",
                action_command=self._open_add_modal
            ).pack(fill="both", expand=True, pady=30)
            return

        for idx, med in enumerate(medicines):
            row_bg = "transparent" if idx % 2 == 0 else Theme.BG_MUTED
            row = ctk.CTkFrame(self.table_scroll, fg_color=row_bg, corner_radius=6, height=44)
            row.pack(fill="x", pady=2)

            # Code Badge
            code_box = ctk.CTkFrame(row, fg_color="transparent", width=120)
            code_box.pack(side="left", padx=8)
            StatusBadge(code_box, text=med["medicine_code"], variant="info").pack(anchor="w")

            # Brand Name & Rx Tag
            name_box = ctk.CTkFrame(row, fg_color="transparent", width=190)
            name_box.pack(side="left", padx=8)
            rx_suffix = " [Rx]" if med.get("prescription_required") else ""
            ctk.CTkLabel(
                name_box,
                text=f"{med['name']}{rx_suffix}",
                font=accessibility_manager.get_font(13, weight="bold"),
                text_color=Theme.TEXT_MAIN,
                anchor="w"
            ).pack(anchor="w")

            # Generic Compound
            ctk.CTkLabel(
                row,
                text=med.get("generic_name") or "—",
                width=150,
                anchor="w",
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MUTED
            ).pack(side="left", padx=8)

            # Category
            ctk.CTkLabel(
                row,
                text=med.get("category_name") or "—",
                width=120,
                anchor="w",
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=8)

            # Stock with Status Badge (TQM Visual Management)
            stock = med.get("total_stock", 0)
            reorder = med.get("reorder_level", 10)
            stock_box = ctk.CTkFrame(row, fg_color="transparent", width=110)
            stock_box.pack(side="left", padx=8)

            if stock == 0:
                StatusBadge(stock_box, text="0 Stock", variant="danger").pack(expand=True)
            elif stock <= reorder:
                StatusBadge(stock_box, text=f"{stock} Low", variant="warning").pack(expand=True)
            else:
                StatusBadge(stock_box, text=f"{stock} In Stock", variant="success").pack(expand=True)

            # Active / Archived status badge
            status_box = ctk.CTkFrame(row, fg_color="transparent", width=80)
            status_box.pack(side="left", padx=8)
            is_active = med.get("is_active", True)
            StatusBadge(status_box, text="Active" if is_active else "Archived", variant="success" if is_active else "neutral").pack(expand=True)

            # Actions
            act_frame = ctk.CTkFrame(row, fg_color="transparent", width=110)
            act_frame.pack(side="left", padx=8)

            ctk.CTkButton(
                act_frame,
                text="✏️",
                width=34,
                height=28,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                command=lambda m=med: self._open_edit_modal(m),
                font=accessibility_manager.get_font(12)
            ).pack(side="left", padx=2)

            if is_active:
                ctk.CTkButton(
                    act_frame,
                    text="Archive",
                    width=62,
                    height=28,
                    fg_color=Theme.SECONDARY,
                    hover_color="#FEE2E2",
                    text_color=Theme.TEXT_MUTED,
                    command=lambda m=med: self._confirm_archive(m),
                    font=accessibility_manager.get_font(11)
                ).pack(side="left", padx=2)

    def _confirm_archive(self, med):
        ConfirmDialog(
            self,
            title="Archive Medicine",
            message=f"Archive '{med['name']}' from active catalog?\n\n"
                    f"Existing sales and batch records will be preserved for audits, but new purchases will be restricted.",
            confirm_text="Archive Product",
            is_destructive=True,
            on_confirm=lambda: self._execute_archive(med["id"])
        )

    def _execute_archive(self, med_id):
        def _do():
            try:
                self.api_client.deactivate_medicine(med_id)
                self.after(0, self.load_medicines)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_do, daemon=True).start()

    def _render_error(self, err_msg):
        self.status_lbl.configure(text=f"Error: {err_msg}", text_color=Theme.DANGER_TEXT)
