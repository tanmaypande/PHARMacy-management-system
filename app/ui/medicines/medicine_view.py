"""
Medicines Formulary Catalog View.
Integrated with responsive DataTable, multi-criteria filtering, pagination, DetailModal, and MedicineModal.
"""
import threading
from typing import Optional, Dict, Any, List
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge
from app.ui.components.dialogs import ConfirmDialog, DetailModal
from app.ui.components.data_table import DataTable


class MedicineModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, medicine=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.medicine = medicine
        self.on_success = on_success
        self.categories_map = {}

        self.title("Edit Medicine" if medicine else "Register New Medicine")
        self.geometry("540x650")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()
        self._load_categories()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=20)

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
        self.entry_code.pack(fill="x", pady=(2, 8))
        if self.medicine:
            self.entry_code.insert(0, self.medicine.get("medicine_code", ""))

        # Brand Name
        ctk.CTkLabel(container, text="Trade / Brand Name *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(container, placeholder_text="e.g. Paracetamol Extra 500mg", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_name.pack(fill="x", pady=(2, 8))
        if self.medicine:
            self.entry_name.insert(0, self.medicine.get("name", ""))

        # Generic Name
        ctk.CTkLabel(container, text="Generic Chemical Compound", font=accessibility_manager.get_font(13), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_generic = ctk.CTkEntry(container, placeholder_text="e.g. Acetaminophen", height=38, border_color=Theme.BORDER, font=accessibility_manager.get_font(13))
        self.entry_generic.pack(fill="x", pady=(2, 8))
        if self.medicine and self.medicine.get("generic_name"):
            self.entry_generic.insert(0, self.medicine.get("generic_name", ""))

        # Category Dropdown
        ctk.CTkLabel(container, text="Therapeutic Category *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.category_var = ctk.StringVar(value="Loading categories...")
        self.category_opt = ctk.CTkOptionMenu(container, variable=self.category_var, values=["Loading..."], height=38, font=accessibility_manager.get_font(13))
        self.category_opt.pack(fill="x", pady=(2, 8))

        # 2 Columns for Manufacturer & Unit
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

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
        checks_row.pack(fill="x", pady=(6, 10))

        self.rx_var = ctk.BooleanVar(value=self.medicine.get("prescription_required", False) if self.medicine else False)
        ctk.CTkCheckBox(checks_row, text="Prescription Required (Rx Only)", variable=self.rx_var, font=accessibility_manager.get_font(12)).pack(side="left")

        self.active_var = ctk.BooleanVar(value=self.medicine.get("is_active", True) if self.medicine else True)
        ctk.CTkCheckBox(checks_row, text="Active in Catalog", variable=self.active_var, font=accessibility_manager.get_font(12)).pack(side="right")

        self.lbl_error = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(12))
        self.lbl_error.pack(anchor="w", pady=(0, 8))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="Save Product",
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

    def _on_err(self, msg: str):
        self.btn_save.configure(state="normal", text="Save Product")
        clean_msg = msg.replace("RuntimeError: ", "")
        self.lbl_error.configure(text=clean_msg)


class MedicineView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.raw_medicines: List[Dict[str, Any]] = []

        self._build_ui()
        self.load_medicines()

    def _build_ui(self):
        # Action Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="💊 Medicines Formulary & Master Catalog",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading products from PostgreSQL database...",
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
            command=self.load_medicines,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ New Medicine",
            width=140,
            height=36,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_add_modal,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        # Multi-Criteria Filter Bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Search brand name, SKU, or generic composition...",
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", self._apply_filters)

        # Stock Filter Dropdown
        self.stock_filter_var = ctk.StringVar(value="All Stock Levels")
        self.stock_filter_opt = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.stock_filter_var,
            values=["All Stock Levels", "In Stock Only", "Low Stock (≤10)", "Out of Stock (0)"],
            height=36,
            width=150,
            font=accessibility_manager.get_font(12),
            command=lambda v: self._apply_filters()
        )
        self.stock_filter_opt.pack(side="left", padx=(0, 8))

        # Status Filter Dropdown
        self.status_filter_var = ctk.StringVar(value="All Statuses")
        self.status_filter_opt = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.status_filter_var,
            values=["All Statuses", "Active Only", "Inactive Only"],
            height=36,
            width=130,
            font=accessibility_manager.get_font(12),
            command=lambda v: self._apply_filters()
        )
        self.status_filter_opt.pack(side="left")

        # DataTable
        columns = [
            {"key": "medicine_code", "title": "SKU Code", "weight": 2, "sortable": True, "formatter": self._format_sku},
            {"key": "name", "title": "Product / Brand Name", "weight": 3, "sortable": True},
            {"key": "category_name", "title": "Therapeutic Class", "weight": 2, "sortable": True},
            {"key": "unit_of_measurement", "title": "Unit", "weight": 1, "sortable": True},
            {"key": "total_stock", "title": "In Stock", "weight": 2, "sortable": True, "formatter": self._format_stock},
            {"key": "is_active", "title": "Status", "weight": 1, "sortable": True, "formatter": self._format_status}
        ]

        actions = [
            {"icon": "👁 View", "width": 58, "command": self._view_details},
            {"icon": "✏ Edit", "width": 54, "command": self._open_edit_modal},
            {"icon": "🗑 Archive", "width": 68, "fg_color": Theme.DANGER_BG, "hover_color": "#FCA5A5", "text_color": Theme.DANGER_TEXT, "command": self._prompt_archive}
        ]

        self.table = DataTable(
            self,
            columns=columns,
            actions=actions,
            page_size=10,
            empty_title="No Medicines Match Criteria",
            empty_desc="Try clearing the search or category filters, or click '➕ New Medicine' to register a new product."
        )
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _format_sku(self, parent, val, row):
        return ctk.CTkLabel(
            parent,
            text=str(val or "—"),
            font=ctk.CTkFont(family="Consolas", size=accessibility_manager.get_font_size(12), weight="bold"),
            text_color=Theme.PRIMARY,
            anchor="w"
        )

    def _format_stock(self, parent, val, row):
        stock = val if val is not None else 0
        reorder = row.get("reorder_level", 10)
        unit = row.get("unit_of_measurement", "Units")

        if stock == 0:
            return StatusBadge(parent, text=f"0 {unit} (Out of Stock)", variant="danger")
        elif stock <= reorder:
            return StatusBadge(parent, text=f"{stock} {unit} (Low)", variant="warning")
        else:
            return StatusBadge(parent, text=f"{stock} {unit}", variant="success")

    def _format_status(self, parent, val, row):
        if val:
            return StatusBadge(parent, text="Active", variant="success")
        return StatusBadge(parent, text="Inactive", variant="neutral")

    def _view_details(self, medicine):
        details = {
            "Product Name": medicine.get("name"),
            "SKU / Code": medicine.get("medicine_code"),
            "Generic Composition": medicine.get("generic_name") or "None Specified",
            "Category": medicine.get("category_name") or "Unclassified",
            "Formulation Unit": medicine.get("unit_of_measurement"),
            "Manufacturer": medicine.get("manufacturer") or "Unlisted",
            "Physical Stock": f"{medicine.get('total_stock', 0)} Units On-Hand",
            "Reorder Threshold": f"{medicine.get('reorder_level', 10)} Units",
            "Prescription Required": "Yes (Rx Required)" if medicine.get("prescription_required") else "No (Over The Counter)",
            "Catalog Active": "Active in Formulary" if medicine.get("is_active") else "Inactive / Archived",
            "Record ID": medicine.get("id")
        }
        DetailModal(self.winfo_toplevel(), title="Medicine Formulary Details", subtitle="Clinical Master Specification", data_dict=details)

    def _open_add_modal(self):
        MedicineModal(self.winfo_toplevel(), self.api_client, on_success=self.load_medicines)

    def _open_edit_modal(self, medicine):
        MedicineModal(self.winfo_toplevel(), self.api_client, medicine=medicine, on_success=self.load_medicines)

    def _prompt_archive(self, medicine):
        ConfirmDialog(
            self.winfo_toplevel(),
            title=f"Archive '{medicine['name']}'?",
            message="Archiving will deactivate this product from the active catalog and POS checkout while preserving historical audit logs.",
            confirm_text="Archive Medicine",
            is_destructive=True,
            on_confirm=lambda: self._execute_archive(medicine["id"])
        )

    def _execute_archive(self, med_id: str):
        def _do():
            try:
                self.api_client.deactivate_medicine(med_id)
                self.after(0, self.load_medicines)
            except Exception as e:
                self.after(0, lambda: self.lbl_count.configure(text=f"Error: {e}", text_color=Theme.DANGER_TEXT))

        threading.Thread(target=_do, daemon=True).start()

    def _apply_filters(self, event=None):
        q = self.search_entry.get().strip().lower()
        stock_filter = self.stock_filter_var.get()
        status_filter = self.status_filter_var.get()

        def match(m):
            # 1. Text search
            text_match = True
            if q:
                name_match = q in m.get("name", "").lower()
                sku_match = q in m.get("medicine_code", "").lower()
                gen_match = bool(m.get("generic_name") and q in m["generic_name"].lower())
                cat_match = bool(m.get("category_name") and q in m["category_name"].lower())
                text_match = (name_match or sku_match or gen_match or cat_match)

            if not text_match:
                return False

            # 2. Stock filter
            stock = m.get("total_stock", 0)
            reorder = m.get("reorder_level", 10)
            if stock_filter == "In Stock Only" and stock <= 0:
                return False
            if stock_filter == "Low Stock (≤10)" and (stock > reorder or stock == 0):
                return False
            if stock_filter == "Out of Stock (0)" and stock > 0:
                return False

            # 3. Status filter
            if status_filter == "Active Only" and not m.get("is_active"):
                return False
            if status_filter == "Inactive Only" and m.get("is_active"):
                return False

            return True

        self.table.filter(match)

    def load_medicines(self):
        self.lbl_count.configure(text="⏳ Querying database via FastAPI...", text_color=Theme.TEXT_MUTED)

        def _fetch():
            try:
                meds = self.api_client.list_medicines()
                self.after(0, self._render_medicines, meds)
            except Exception as e:
                self.after(0, lambda: self.lbl_count.configure(text=f"API Error: {e}", text_color=Theme.DANGER_TEXT))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_medicines(self, medicines):
        self.raw_medicines = medicines or []
        self.lbl_count.configure(
            text=f"Total: {len(self.raw_medicines)} products registered in PostgreSQL formulary",
            text_color=Theme.TEXT_MUTED
        )
        self.table.set_data(self.raw_medicines)
