"""
Wholesale Pharmaceutical Suppliers Management View.
Integrated with live search, data table, add/edit modals, and accessibility standards.
"""
from typing import Optional, Dict, Any, List
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.badge import StatusBadge
from app.ui.components.dialogs import ConfirmDialog
from app.ui.components.data_table import DataTable


class SupplierModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, supplier=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.supplier = supplier
        self.on_success = on_success

        self.title("Edit Supplier" if supplier else "Register New Supplier")
        self.geometry("480x480")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        title = "Edit Supplier Details" if self.supplier else "Register Pharmaceutical Distributor"
        ctk.CTkLabel(
            container,
            text=title,
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            container,
            text="Licensed wholesale vendor for inbound batch procurement",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Name
        ctk.CTkLabel(container, text="Supplier Company Name *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(container, placeholder_text="e.g. Apex Pharma Distributors", height=36)
        self.entry_name.pack(fill="x", pady=(2, 8))
        if self.supplier:
            self.entry_name.insert(0, self.supplier.get("name", ""))

        # Contact Person & Phone
        row = ctk.CTkFrame(container, fg_color="transparent")
        row.pack(fill="x", pady=(0, 8))

        c1 = ctk.CTkFrame(row, fg_color="transparent")
        c1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(c1, text="Contact Person", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_contact = ctk.CTkEntry(c1, placeholder_text="e.g. Rajesh Kumar", height=36)
        self.entry_contact.pack(fill="x", pady=(2, 0))
        if self.supplier and self.supplier.get("contact_person"):
            self.entry_contact.insert(0, self.supplier["contact_person"])

        c2 = ctk.CTkFrame(row, fg_color="transparent")
        c2.pack(side="right", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(c2, text="Phone Number", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_phone = ctk.CTkEntry(c2, placeholder_text="e.g. +91 98765 00000", height=36)
        self.entry_phone.pack(fill="x", pady=(2, 0))
        if self.supplier and self.supplier.get("phone"):
            self.entry_phone.insert(0, self.supplier["phone"])

        # Email
        ctk.CTkLabel(container, text="Email Address", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_email = ctk.CTkEntry(container, placeholder_text="e.g. orders@apexpharma.com", height=36)
        self.entry_email.pack(fill="x", pady=(2, 8))
        if self.supplier and self.supplier.get("email"):
            self.entry_email.insert(0, self.supplier["email"])

        # Address
        ctk.CTkLabel(container, text="Warehouse / Depot Address", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_addr = ctk.CTkEntry(container, placeholder_text="e.g. Plot 42, Pharma Industrial Estate", height=36)
        self.entry_addr.pack(fill="x", pady=(2, 14))
        if self.supplier and self.supplier.get("address"):
            self.entry_addr.insert(0, self.supplier["address"])

        self.lbl_err = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(11))
        self.lbl_err.pack(anchor="w", pady=(0, 8))

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_box,
            text="Save Supplier",
            height=38,
            fg_color=Theme.PRIMARY,
            command=self._save
        )
        self.btn_save.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            height=38,
            fg_color=Theme.SECONDARY,
            text_color=Theme.SECONDARY_TEXT,
            command=self.destroy
        ).pack(side="right", padx=(6, 0))

    def _save(self):
        name = self.entry_name.get().strip()
        if not name:
            self.lbl_err.configure(text="Supplier company name is required.")
            return

        payload = {
            "name": name,
            "contact_person": self.entry_contact.get().strip() or None,
            "phone": self.entry_phone.get().strip() or None,
            "email": self.entry_email.get().strip() or None,
            "address": self.entry_addr.get().strip() or None,
            "is_active": True
        }

        self.btn_save.configure(state="disabled", text="Saving...")

        def _do():
            if self.supplier:
                return self.api_client.update_supplier(self.supplier["id"], payload)
            else:
                return self.api_client.create_supplier(payload)

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
        self.btn_save.configure(state="normal", text="Save Supplier")
        self.lbl_err.configure(text=str(err).replace("RuntimeError: ", ""))


class SupplierView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.suppliers_list = []

        self._build_ui()
        self.load_suppliers()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🏢 Wholesale Pharmaceutical Suppliers",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading suppliers...",
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
            command=self.load_suppliers
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ New Supplier",
            width=130,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._open_add_modal
        ).pack(side="left", padx=5)

        # Search Bar
        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="🔍 Search supplier by name, contact person, or phone number...",
            height=36
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        # Table
        self.columns = [
            {"key": "name", "title": "Supplier Name", "width": 240, "anchor": "w"},
            {"key": "contact_person", "title": "Contact Person", "width": 160, "anchor": "w"},
            {"key": "phone", "title": "Phone Number", "width": 140, "anchor": "w"},
            {"key": "email", "title": "Email Address", "width": 200, "anchor": "w"},
            {"key": "address", "title": "Depot Address", "width": 220, "anchor": "w"},
            {"key": "actions", "title": "Actions", "width": 140, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=self.columns, rows_per_page=12)
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def load_suppliers(self):
        self.lbl_count.configure(text="Fetching suppliers from database...")
        run_in_background(
            lambda: self.api_client.list_suppliers(),
            on_success=self._on_loaded,
            on_error=lambda err: self.lbl_count.configure(text=f"Error: {err}")
        )

    def _on_loaded(self, suppliers):
        self.suppliers_list = suppliers or []
        self.lbl_count.configure(text=f"Total: {len(self.suppliers_list)} verified distributors")
        self._render_table(self.suppliers_list)

    def _on_search(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self._render_table(self.suppliers_list)
            return

        filtered = [
            s for s in self.suppliers_list
            if query in s.get("name", "").lower()
            or query in (s.get("contact_person") or "").lower()
            or query in (s.get("phone") or "").lower()
        ]
        self._render_table(filtered)

    def _render_table(self, data):
        rows = []
        for s in data:
            rows.append({
                "name": s.get("name", ""),
                "contact_person": s.get("contact_person") or "—",
                "phone": s.get("phone") or "—",
                "email": s.get("email") or "—",
                "address": s.get("address") or "—",
                "_raw": s
            })

        def action_builder(parent, row):
            box = ctk.CTkFrame(parent, fg_color="transparent")
            ctk.CTkButton(
                box,
                text="✏️",
                width=32,
                height=26,
                fg_color=Theme.SECONDARY,
                text_color=Theme.SECONDARY_TEXT,
                command=lambda raw=row["_raw"]: self._open_edit_modal(raw)
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                box,
                text="🗑️",
                width=32,
                height=26,
                fg_color=Theme.DANGER_BG,
                text_color=Theme.DANGER_TEXT,
                command=lambda raw=row["_raw"]: self._delete_supplier(raw)
            ).pack(side="left", padx=2)
            return box

        self.table.set_data(rows, action_builder=action_builder)

    def _open_add_modal(self):
        SupplierModal(self.winfo_toplevel(), self.api_client, on_success=self.load_suppliers)

    def _open_edit_modal(self, supplier):
        SupplierModal(self.winfo_toplevel(), self.api_client, supplier=supplier, on_success=self.load_suppliers)

    def _delete_supplier(self, supplier):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Delete Supplier",
            message=f"Are you sure you want to delete supplier '{supplier['name']}'?",
            confirm_label="Delete",
            danger=True,
            on_confirm=lambda: run_in_background(
                lambda: self.api_client.delete_supplier(supplier["id"]),
                on_success=lambda _: self.load_suppliers()
            )
        )
