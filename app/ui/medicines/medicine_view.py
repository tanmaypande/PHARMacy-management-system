import threading
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.accessibility.accessibility_manager import accessibility_manager


class MedicineModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, medicine=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.medicine = medicine
        self.on_success = on_success
        self.categories_map = {}  # name -> id

        self.title("Edit Medicine" if medicine else "Add New Medicine")
        self.geometry("520x620")
        self.resizable(False, False)
        self.grab_set()

        self._build_form()
        self._load_categories()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        title_text = "Edit Pharmaceutical Product" if self.medicine else "Register New Medicine Catalog Item"
        ctk.CTkLabel(
            container,
            text=title_text,
            font=accessibility_manager.get_font(18, weight="bold")
        ).pack(anchor="w", pady=(0, 15))

        # Medicine Code
        ctk.CTkLabel(container, text="Medicine Code / SKU *", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.entry_code = ctk.CTkEntry(container, placeholder_text="e.g. MED-PARA-500", height=36, font=accessibility_manager.get_font(13))
        self.entry_code.pack(fill="x", pady=(2, 10))
        if self.medicine:
            self.entry_code.insert(0, self.medicine.get("medicine_code", ""))

        # Brand Name
        ctk.CTkLabel(container, text="Brand / Trade Name *", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(container, placeholder_text="e.g. Paracetamol Extra 500mg", height=36, font=accessibility_manager.get_font(13))
        self.entry_name.pack(fill="x", pady=(2, 10))
        if self.medicine:
            self.entry_name.insert(0, self.medicine.get("name", ""))

        # Generic Name
        ctk.CTkLabel(container, text="Generic Chemical Compound", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.entry_generic = ctk.CTkEntry(container, placeholder_text="e.g. Acetaminophen", height=36, font=accessibility_manager.get_font(13))
        self.entry_generic.pack(fill="x", pady=(2, 10))
        if self.medicine and self.medicine.get("generic_name"):
            self.entry_generic.insert(0, self.medicine.get("generic_name", ""))

        # Category Dropdown
        ctk.CTkLabel(container, text="Drug Category *", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.category_var = ctk.StringVar(value="Loading categories...")
        self.category_opt = ctk.CTkOptionMenu(container, variable=self.category_var, values=["Loading..."], height=36, font=accessibility_manager.get_font(13))
        self.category_opt.pack(fill="x", pady=(2, 10))

        # 2 Columns for Manufacturer & Unit
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 10))

        col_mfg = ctk.CTkFrame(row1, fg_color="transparent")
        col_mfg.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkLabel(col_mfg, text="Manufacturer", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.entry_mfg = ctk.CTkEntry(col_mfg, placeholder_text="e.g. GSK, Pfizer", height=36, font=accessibility_manager.get_font(13))
        self.entry_mfg.pack(fill="x", pady=(2, 0))
        if self.medicine and self.medicine.get("manufacturer"):
            self.entry_mfg.insert(0, self.medicine.get("manufacturer", ""))

        col_unit = ctk.CTkFrame(row1, fg_color="transparent")
        col_unit.pack(side="right", expand=True, fill="x", padx=(5, 0))
        ctk.CTkLabel(col_unit, text="Unit of Measure", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.unit_var = ctk.StringVar(value=self.medicine.get("unit_of_measurement", "Tablets") if self.medicine else "Tablets")
        self.unit_opt = ctk.CTkOptionMenu(
            col_unit,
            variable=self.unit_var,
            values=["Tablets", "Capsules", "Syrup (Bottle)", "Strip", "Vial", "Ointment (Tube)", "Drops"],
            height=36,
            font=accessibility_manager.get_font(13)
        )
        self.unit_opt.pack(fill="x", pady=(2, 0))

        # Checkboxes row: Rx required & Active status
        checks_row = ctk.CTkFrame(container, fg_color="transparent")
        checks_row.pack(fill="x", pady=(5, 12))

        self.rx_var = ctk.BooleanVar(value=self.medicine.get("prescription_required", False) if self.medicine else False)
        ctk.CTkCheckBox(checks_row, text="Prescription Required (Rx)", variable=self.rx_var, font=accessibility_manager.get_font(13)).pack(side="left")

        self.active_var = ctk.BooleanVar(value=self.medicine.get("is_active", True) if self.medicine else True)
        ctk.CTkCheckBox(checks_row, text="Active in Catalog", variable=self.active_var, font=accessibility_manager.get_font(13)).pack(side="right")

        self.lbl_error = ctk.CTkLabel(container, text="", text_color="#EF4444", font=accessibility_manager.get_font(12))
        self.lbl_error.pack(anchor="w", pady=(0, 10))

        # Actions
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="Save Medicine",
            height=40,
            command=self._save,
            font=accessibility_manager.get_font(14, weight="bold")
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            height=40,
            fg_color="#64748B",
            command=self.destroy,
            font=accessibility_manager.get_font(14)
        ).pack(side="right", padx=(10, 0))

    def _load_categories(self):
        def _fetch():
            try:
                cats = self.api_client.list_categories()
                self.after(0, self._populate_categories, cats)
            except Exception as e:
                self.after(0, self._on_err, f"Failed to load categories: {e}")

        threading.Thread(target=_fetch, daemon=True).start()

    def _populate_categories(self, categories):
        if not categories:
            self.category_opt.configure(values=["No categories found - Add one first"])
            self.category_var.set("No categories found - Add one first")
            return

        self.categories_map = {c["name"]: c["id"] for c in categories}
        cat_names = list(self.categories_map.keys())
        self.category_opt.configure(values=cat_names)

        # Set default
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

        cat_id = self.categories_map[cat_name]

        payload = {
            "medicine_code": code,
            "name": name,
            "generic_name": generic,
            "category_id": cat_id,
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
        self.btn_save.configure(state="normal", text="Save Medicine")
        self.lbl_error.configure(text=err_msg.replace("RuntimeError: ", ""))


class MedicineView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.categories_map = {}
        self._build_ui()
        self.load_medicines()

    def _build_ui(self):
        # Header Row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="💊 Medicine Catalog & Master Data",
            font=accessibility_manager.get_font(20, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="➕ Register Medicine",
            width=160,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._open_add_modal,
            font=accessibility_manager.get_font(13, weight="bold")
        ).pack(side="right")

        # Filter & Search Bar
        filter_bar = ctk.CTkFrame(self, fg_color=accessibility_manager.get_card_fg(), corner_radius=10)
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.entry_search = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Search brand name, generic chemical, or code...",
            width=300,
            height=36,
            font=accessibility_manager.get_font(13)
        )
        self.entry_search.pack(side="left", padx=15, pady=10)
        self.entry_search.bind("<Return>", lambda e: self.load_medicines())

        ctk.CTkButton(
            filter_bar,
            text="Search",
            width=80,
            command=self.load_medicines,
            font=accessibility_manager.get_font(13)
        ).pack(side="left", padx=(0, 15))

        self.cat_filter_var = ctk.StringVar(value="All Categories")
        self.cat_filter_opt = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.cat_filter_var,
            values=["All Categories"],
            command=lambda v: self.load_medicines(),
            height=36,
            font=accessibility_manager.get_font(13)
        )
        self.cat_filter_opt.pack(side="left", padx=5)

        ctk.CTkButton(
            filter_bar,
            text="Reset",
            width=70,
            fg_color="#64748B",
            command=self._reset_filters,
            font=accessibility_manager.get_font(12)
        ).pack(side="right", padx=15)

        # Status text
        self.status_lbl = ctk.CTkLabel(self, text="Loading medicines...", font=accessibility_manager.get_font(13), text_color="#94A3B8")
        self.status_lbl.pack(anchor="w", padx=20, pady=(0, 5))

        # Scrollable table container
        self.table_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=accessibility_manager.get_card_fg(),
            corner_radius=10
        )
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))

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

        self.status_lbl.configure(text="⏳ Querying medicine catalog...", text_color="#FBBF24")

        def _fetch():
            try:
                # Also refresh categories for filter dropdown
                cats = self.api_client.list_categories()
                meds = self.api_client.list_medicines(search=search_query, category_id=cat_id)
                self.after(0, self._render_results, meds, cats)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_results(self, medicines, categories):
        # Update category filter dropdown
        self.categories_map = {c["name"]: c["id"] for c in categories}
        dropdown_vals = ["All Categories"] + list(self.categories_map.keys())
        self.cat_filter_opt.configure(values=dropdown_vals)

        # Clear existing
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        self.status_lbl.configure(text=f"Showing {len(medicines)} medicines matching criteria", text_color="#34D399")

        if not medicines:
            ctk.CTkLabel(
                self.table_scroll,
                text="No medicines found. Click '➕ Register Medicine' to add items.",
                font=accessibility_manager.get_font(14)
            ).pack(pady=40)
            return

        # Table Header
        hdr = ctk.CTkFrame(self.table_scroll, fg_color="#334155", height=36)
        hdr.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(hdr, text="Code / SKU", width=120, anchor="w", font=accessibility_manager.get_font(12, weight="bold")).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Brand Name", width=180, anchor="w", font=accessibility_manager.get_font(12, weight="bold")).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Generic Compound", width=160, anchor="w", font=accessibility_manager.get_font(12, weight="bold")).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Category", width=120, anchor="w", font=accessibility_manager.get_font(12, weight="bold")).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Stock", width=80, anchor="center", font=accessibility_manager.get_font(12, weight="bold")).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Status", width=80, anchor="center", font=accessibility_manager.get_font(12, weight="bold")).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Actions", width=130, anchor="center", font=accessibility_manager.get_font(12, weight="bold")).pack(side="left", padx=8)

        for med in medicines:
            row = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=4)

            ctk.CTkLabel(row, text=med["medicine_code"], width=120, anchor="w", font=accessibility_manager.get_font(12, weight="bold"), text_color="#38BDF8").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=med["name"], width=180, anchor="w", font=accessibility_manager.get_font(12)).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=med.get("generic_name") or "—", width=160, anchor="w", font=accessibility_manager.get_font(12), text_color="#94A3B8").pack(side="left", padx=8)
            ctk.CTkLabel(row, text=med.get("category_name") or "—", width=120, anchor="w", font=accessibility_manager.get_font(12)).pack(side="left", padx=8)

            # Stock with color badge
            stock = med.get("total_stock", 0)
            stock_color = "#34D399" if stock > med.get("reorder_level", 10) else ("#F87171" if stock == 0 else "#FBBF24")
            stock_lbl = ctk.CTkLabel(row, text=f"{stock} {med.get('unit_of_measurement')[:3]}", width=80, anchor="center", font=accessibility_manager.get_font(12, weight="bold"), text_color=stock_color)
            stock_lbl.pack(side="left", padx=8)

            # Active status badge
            is_active = med.get("is_active", True)
            status_text = "Active" if is_active else "Inactive"
            status_color = "#34D399" if is_active else "#94A3B8"
            ctk.CTkLabel(row, text=status_text, width=80, anchor="center", font=accessibility_manager.get_font(11), text_color=status_color).pack(side="left", padx=8)

            # Actions
            act_frame = ctk.CTkFrame(row, fg_color="transparent", width=130)
            act_frame.pack(side="left", padx=8)

            ctk.CTkButton(
                act_frame,
                text="✏️",
                width=35,
                height=26,
                command=lambda m=med: self._open_edit_modal(m),
                font=accessibility_manager.get_font(12)
            ).pack(side="left", padx=2)

            if is_active:
                ctk.CTkButton(
                    act_frame,
                    text="Archive",
                    width=65,
                    height=26,
                    fg_color="#64748B",
                    hover_color="#475569",
                    command=lambda m=med: self._deactivate_medicine(m),
                    font=accessibility_manager.get_font(11)
                ).pack(side="left", padx=2)

    def _deactivate_medicine(self, med):
        def _do():
            try:
                self.api_client.deactivate_medicine(med["id"])
                self.after(0, self.load_medicines)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_do, daemon=True).start()

    def _render_error(self, err_msg):
        self.status_lbl.configure(text=f"Error: {err_msg}", text_color="#EF4444")
