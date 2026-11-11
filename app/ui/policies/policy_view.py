"""
Pharmacy Governance Policies & Standard Operating Procedures (SOP) Module.
Maintains clinical store governance, medicine handling rules, cold chain protocols, and audit review cycles.
"""
from typing import Optional, Dict, Any, List
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.dialogs import ConfirmDialog
from app.ui.components.data_table import DataTable


class PolicyModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, policy=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.policy = policy
        self.on_success = on_success

        self.title("Edit Standard Operating Procedure" if policy else "Create Pharmacy Policy / SOP")
        self.geometry("540x560")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        title = "Edit Policy Details" if self.policy else "Register Pharmacy SOP / Policy"
        ctk.CTkLabel(
            container,
            text=title,
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text="Standard Operating Procedures governing dispensing, cold-chain storage, and clinical safety",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Title
        ctk.CTkLabel(container, text="Policy / SOP Title *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_title = ctk.CTkEntry(container, placeholder_text="e.g. Schedule H Drug Dispensing Verification Protocol", height=36)
        self.entry_title.pack(fill="x", pady=(2, 8))
        if self.policy:
            self.entry_title.insert(0, self.policy.get("title", ""))

        # Category & Role
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        c_cat = ctk.CTkFrame(row1, fg_color="transparent")
        c_cat.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(c_cat, text="Governance Category *", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.cat_var = ctk.StringVar(value=self.policy.get("category", "Store Governance") if self.policy else "Store Governance")
        self.cat_opt = ctk.CTkOptionMenu(
            c_cat,
            variable=self.cat_var,
            values=["Store Governance", "Medicine Storage & Cold Chain", "Prescription Verification", "Expiry & Quarantine", "Data Security & HIPAA"],
            height=36
        )
        self.cat_opt.pack(fill="x", pady=(2, 0))

        c_role = ctk.CTkFrame(row1, fg_color="transparent")
        c_role.pack(side="right", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(c_role, text="Responsible Staff Role *", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.role_var = ctk.StringVar(value=self.policy.get("responsible_role", "All Staff") if self.policy else "All Staff")
        self.role_opt = ctk.CTkOptionMenu(
            c_role,
            variable=self.role_var,
            values=["All Staff", "Pharmacist", "Administrator", "Cashier", "Inventory Manager"],
            height=36
        )
        self.role_opt.pack(fill="x", pady=(2, 0))

        # Version
        row_v = ctk.CTkFrame(container, fg_color="transparent")
        row_v.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(row_v, text="Version Number", font=accessibility_manager.get_font(12)).pack(side="left")
        self.entry_ver = ctk.CTkEntry(row_v, width=80, height=32)
        self.entry_ver.pack(side="left", padx=8)
        self.entry_ver.insert(0, self.policy.get("version", "1.0") if self.policy else "1.0")

        # SOP Text
        ctk.CTkLabel(container, text="Full Policy & Procedure Text *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.txt_content = ctk.CTkTextbox(container, height=140, font=accessibility_manager.get_font(11))
        self.txt_content.pack(fill="x", pady=(2, 14))
        if self.policy:
            self.txt_content.insert("1.0", self.policy.get("content", ""))

        self.lbl_err = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(11))
        self.lbl_err.pack(anchor="w", pady=(0, 8))

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_box,
            text="Save Policy",
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
        t = self.entry_title.get().strip()
        c = self.txt_content.get("1.0", "end").strip()
        if not t or not c:
            self.lbl_err.configure(text="Title and Policy content text are required.")
            return

        payload = {
            "title": t,
            "category": self.cat_var.get(),
            "version": self.entry_ver.get().strip() or "1.0",
            "responsible_role": self.role_var.get(),
            "content": c,
            "is_active": True
        }

        self.btn_save.configure(state="disabled", text="Saving...")

        def _do():
            if self.policy:
                return self.api_client.update_policy(self.policy["id"], payload)
            else:
                return self.api_client.create_policy(payload)

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
        self.btn_save.configure(state="normal", text="Save Policy")
        self.lbl_err.configure(text=str(err).replace("RuntimeError: ", ""))


class PolicyView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.policies_list = []

        self._build_ui()
        self.load_policies()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📜 Pharmacy Governance Policies & Standard Operating Procedures (SOP)",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading policies...",
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
            command=self.load_policies
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ New SOP / Policy",
            width=160,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._open_add_modal
        ).pack(side="left", padx=5)

        # Search & Filter
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Search policy by keyword, responsibility, or SOP title...",
            height=36
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        self.cat_filter_var = ctk.StringVar(value="All Categories")
        self.cat_opt = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.cat_filter_var,
            values=["All Categories", "Store Governance", "Medicine Storage & Cold Chain", "Prescription Verification", "Expiry & Quarantine", "Data Security & HIPAA"],
            height=36,
            command=lambda v: self._on_search()
        )
        self.cat_opt.pack(side="right")

        # Table
        self.columns = [
            {"key": "title", "title": "SOP / Policy Title", "width": 260, "anchor": "w"},
            {"key": "category", "title": "Domain Category", "width": 180, "anchor": "w"},
            {"key": "role", "title": "Accountable Role", "width": 130, "anchor": "center"},
            {"key": "version", "title": "Version", "width": 80, "anchor": "center"},
            {"key": "updated", "title": "Last Reviewed", "width": 120, "anchor": "w"},
            {"key": "actions", "title": "Actions", "width": 110, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=self.columns, rows_per_page=10)
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def load_policies(self):
        self.lbl_count.configure(text="Fetching active policies from database...")
        run_in_background(
            lambda: self.api_client.list_policies(),
            on_success=self._on_loaded,
            on_error=lambda err: self.lbl_count.configure(text=f"Error: {err}")
        )

    def _on_loaded(self, policies):
        self.policies_list = policies or []
        self.lbl_count.configure(text=f"Total: {len(self.policies_list)} clinical SOP guidelines enforced")
        self._on_search()

    def _on_search(self):
        query = self.search_entry.get().strip().lower()
        sel_cat = self.cat_filter_var.get()

        filtered = []
        for p in self.policies_list:
            if sel_cat != "All Categories" and p.get("category") != sel_cat:
                continue
            if query and query not in p.get("title", "").lower() and query not in p.get("content", "").lower() and query not in p.get("responsible_role", "").lower():
                continue
            filtered.append(p)

        rows = []
        for p in filtered:
            rows.append({
                "title": p.get("title", ""),
                "category": p.get("category", ""),
                "role": p.get("responsible_role", "All Staff"),
                "version": f"v{p.get('version', '1.0')}",
                "updated": p.get("updated_at", ""),
                "_raw": p
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
                command=lambda raw=row["_raw"]: self._delete_policy(raw)
            ).pack(side="left", padx=2)
            return box

        self.table.set_data(rows, action_builder=action_builder)

    def _open_add_modal(self):
        PolicyModal(self.winfo_toplevel(), self.api_client, on_success=self.load_policies)

    def _open_edit_modal(self, policy):
        PolicyModal(self.winfo_toplevel(), self.api_client, policy=policy, on_success=self.load_policies)

    def _delete_policy(self, policy):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Delete Policy SOP",
            message=f"Are you sure you want to remove policy '{policy['title']}'?",
            confirm_label="Delete",
            danger=True,
            on_confirm=lambda: run_in_background(
                lambda: self.api_client.delete_policy(policy["id"]),
                on_success=lambda _: self.load_policies()
            )
        )
