"""
Role-Based Access Control (RBAC) & Users Management View.
Allows Admin/Owner to provision staff logins, assign permissions, and monitor active sessions.
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


class UserModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.on_success = on_success

        self.title("Provision New User Account")
        self.geometry("460x420")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            container,
            text="Create Employee Account",
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text="Role-based permissions govern access to sensitive pharmacy modules",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Username
        ctk.CTkLabel(container, text="Login Username *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_username = ctk.CTkEntry(container, placeholder_text="e.g. jdoe_pharmacist", height=36)
        self.entry_username.pack(fill="x", pady=(2, 8))

        # Full Name
        ctk.CTkLabel(container, text="Full Staff Name *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(container, placeholder_text="e.g. John Doe, PharmD", height=36)
        self.entry_name.pack(fill="x", pady=(2, 8))

        # Password
        ctk.CTkLabel(container, text="Password *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_pass = ctk.CTkEntry(container, placeholder_text="••••••••", show="•", height=36)
        self.entry_pass.pack(fill="x", pady=(2, 8))

        # Role
        ctk.CTkLabel(container, text="System Role & Authority *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.role_var = ctk.StringVar(value="pharmacist")
        self.role_opt = ctk.CTkOptionMenu(
            container,
            variable=self.role_var,
            values=["admin", "pharmacist", "cashier"],
            height=36
        )
        self.role_opt.pack(fill="x", pady=(2, 14))

        self.lbl_err = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(11))
        self.lbl_err.pack(anchor="w", pady=(0, 8))

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_box,
            text="Create User",
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
        u = self.entry_username.get().strip()
        n = self.entry_name.get().strip()
        p = self.entry_pass.get().strip()
        r = self.role_var.get()

        if not u or not n or not p:
            self.lbl_err.configure(text="All fields are required.")
            return

        payload = {
            "username": u,
            "full_name": n,
            "password": p,
            "role": r
        }

        self.btn_save.configure(state="disabled", text="Creating...")

        def _do():
            return self.api_client.create_user(payload)

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
        self.btn_save.configure(state="normal", text="Create User")
        self.lbl_err.configure(text=str(err).replace("RuntimeError: ", ""))


class UsersView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.users_list = []

        self._build_ui()
        self.load_users()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="👤 User Management & Role Permissions (RBAC)",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading staff accounts...",
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
            command=self.load_users
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ New User",
            width=130,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._open_add_modal
        ).pack(side="left", padx=5)

        # Table
        self.columns = [
            {"key": "username", "title": "Username", "width": 160, "anchor": "w"},
            {"key": "full_name", "title": "Staff Full Name", "width": 220, "anchor": "w"},
            {"key": "role", "title": "Assigned Role", "width": 140, "anchor": "center"},
            {"key": "last_login", "title": "Last Login", "width": 180, "anchor": "w"},
            {"key": "status", "title": "Account Status", "width": 120, "anchor": "center"},
            {"key": "actions", "title": "Actions", "width": 120, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=self.columns, rows_per_page=12)
        self.table.pack(fill="both", expand=True, padx=20, pady=(10, 15))

    def load_users(self):
        self.lbl_count.configure(text="Fetching employee accounts...")
        run_in_background(
            lambda: self.api_client.list_users(),
            on_success=self._on_loaded,
            on_error=lambda err: self.lbl_count.configure(text=f"Error: {err}")
        )

    def _on_loaded(self, users):
        self.users_list = users or []
        self.lbl_count.configure(text=f"Total: {len(self.users_list)} registered staff members")
        rows = []
        for u in self.users_list:
            rows.append({
                "username": u.get("username", ""),
                "full_name": u.get("full_name", ""),
                "role": u.get("role", "cashier").upper(),
                "last_login": u.get("last_login") or "Never",
                "status": "Active" if u.get("is_active") else "Disabled",
                "_raw": u
            })

        def action_builder(parent, row):
            box = ctk.CTkFrame(parent, fg_color="transparent")
            raw = row["_raw"]
            toggle_label = "Deactivate" if raw.get("is_active") else "Activate"
            btn_color = Theme.WARNING_BG if raw.get("is_active") else Theme.SUCCESS_BG
            text_color = Theme.WARNING_TEXT if raw.get("is_active") else Theme.SUCCESS_TEXT

            ctk.CTkButton(
                box,
                text=toggle_label,
                width=80,
                height=26,
                fg_color=btn_color,
                text_color=text_color,
                command=lambda r=raw: self._toggle_user(r)
            ).pack(side="left", padx=2)
            return box

        self.table.set_data(rows, action_builder=action_builder)

    def _open_add_modal(self):
        UserModal(self.winfo_toplevel(), self.api_client, on_success=self.load_users)

    def _toggle_user(self, user):
        run_in_background(
            lambda: self.api_client.toggle_user_active(user["id"]),
            on_success=lambda _: self.load_users()
        )
