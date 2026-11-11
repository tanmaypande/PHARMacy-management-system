"""
Patient & Customer Directory View.
Integrated with live search, patient registry, detail modal, and accessibility standards.
"""
from typing import Optional, Dict, Any, List
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.dialogs import ConfirmDialog
from app.ui.components.data_table import DataTable


class CustomerModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, customer=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.customer = customer
        self.on_success = on_success

        self.title("Edit Patient Record" if customer else "Enroll New Patient / Customer")
        self.geometry("480x420")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        title = "Edit Patient Information" if self.customer else "Enroll New Patient Record"
        ctk.CTkLabel(
            container,
            text=title,
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            container,
            text="Preserves patient profiles, prescription history, and billing records",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Full Name
        ctk.CTkLabel(container, text="Patient Full Name *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(container, placeholder_text="e.g. Ananya Sharma", height=36)
        self.entry_name.pack(fill="x", pady=(2, 8))
        if self.customer:
            self.entry_name.insert(0, self.customer.get("name", ""))

        # Phone Number
        ctk.CTkLabel(container, text="Phone Number *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_phone = ctk.CTkEntry(container, placeholder_text="e.g. +91 98765 12345", height=36)
        self.entry_phone.pack(fill="x", pady=(2, 8))
        if self.customer and self.customer.get("phone"):
            self.entry_phone.insert(0, self.customer["phone"])

        # Email
        ctk.CTkLabel(container, text="Email Address", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_email = ctk.CTkEntry(container, placeholder_text="e.g. ananya@example.com", height=36)
        self.entry_email.pack(fill="x", pady=(2, 8))
        if self.customer and self.customer.get("email"):
            self.entry_email.insert(0, self.customer["email"])

        # Address
        ctk.CTkLabel(container, text="Residential Address", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_addr = ctk.CTkEntry(container, placeholder_text="e.g. Flat 304, Green Park Residency", height=36)
        self.entry_addr.pack(fill="x", pady=(2, 14))
        if self.customer and self.customer.get("address"):
            self.entry_addr.insert(0, self.customer["address"])

        self.lbl_err = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(11))
        self.lbl_err.pack(anchor="w", pady=(0, 8))

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_box,
            text="Save Patient Record",
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
        phone = self.entry_phone.get().strip()
        if not name:
            self.lbl_err.configure(text="Patient name is required.")
            return

        payload = {
            "name": name,
            "phone": phone or None,
            "email": self.entry_email.get().strip() or None,
            "address": self.entry_addr.get().strip() or None
        }

        self.btn_save.configure(state="disabled", text="Saving...")

        def _do():
            if self.customer:
                return self.api_client.update_customer(self.customer["id"], payload)
            else:
                return self.api_client.create_customer(payload)

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
        self.btn_save.configure(state="normal", text="Save Patient Record")
        self.lbl_err.configure(text=str(err).replace("RuntimeError: ", ""))


class CustomerView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.customers_list = []

        self._build_ui()
        self.load_customers()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="👥 Patient & Customer Directory",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading patient records...",
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
            command=self.load_customers
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ Enroll Patient",
            width=140,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._open_add_modal
        ).pack(side="left", padx=5)

        # Search Bar
        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_bar,
            placeholder_text="🔍 Search patient by name, phone number, or email...",
            height=36
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        # Table
        self.columns = [
            {"key": "name", "title": "Patient Name", "width": 220, "anchor": "w"},
            {"key": "phone", "title": "Phone Number", "width": 150, "anchor": "w"},
            {"key": "email", "title": "Email Address", "width": 200, "anchor": "w"},
            {"key": "address", "title": "Residential Address", "width": 240, "anchor": "w"},
            {"key": "actions", "title": "Actions", "width": 140, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=self.columns, rows_per_page=12)
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def load_customers(self):
        self.lbl_count.configure(text="Fetching patients from database...")
        run_in_background(
            lambda: self.api_client.list_customers(),
            on_success=self._on_loaded,
            on_error=lambda err: self.lbl_count.configure(text=f"Error: {err}")
        )

    def _on_loaded(self, customers):
        self.customers_list = customers or []
        self.lbl_count.configure(text=f"Total: {len(self.customers_list)} enrolled patients")
        self._render_table(self.customers_list)

    def _on_search(self):
        query = self.search_entry.get().strip().lower()
        if not query:
            self._render_table(self.customers_list)
            return

        filtered = [
            c for c in self.customers_list
            if query in c.get("name", "").lower()
            or query in (c.get("phone") or "").lower()
            or query in (c.get("email") or "").lower()
        ]
        self._render_table(filtered)

    def _render_table(self, data):
        rows = []
        for c in data:
            rows.append({
                "name": c.get("name", ""),
                "phone": c.get("phone") or "—",
                "email": c.get("email") or "—",
                "address": c.get("address") or "—",
                "_raw": c
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
                command=lambda raw=row["_raw"]: self._delete_customer(raw)
            ).pack(side="left", padx=2)
            return box

        self.table.set_data(rows, action_builder=action_builder)

    def _open_add_modal(self):
        CustomerModal(self.winfo_toplevel(), self.api_client, on_success=self.load_customers)

    def _open_edit_modal(self, customer):
        CustomerModal(self.winfo_toplevel(), self.api_client, customer=customer, on_success=self.load_customers)

    def _delete_customer(self, customer):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Delete Patient Record",
            message=f"Are you sure you want to remove patient '{customer['name']}'?",
            confirm_label="Delete",
            danger=True,
            on_confirm=lambda: run_in_background(
                lambda: self.api_client.delete_customer(customer["id"]),
                on_success=lambda _: self.load_customers()
            )
        )
