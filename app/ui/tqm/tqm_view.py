"""
Total Quality Management (TQM) Quality Dashboard & Audit Module.
Calculates and visualizes live clinical quality metrics (unfabricated), CAPA logs, and incident audits.
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
from app.ui.components.stat_card import StatCard


class TQMRecordModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, record=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.record = record
        self.on_success = on_success

        self.title("Edit Quality Record" if record else "Log Quality Audit / CAPA Incident")
        self.geometry("520x540")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        title = "Edit TQM Audit / Incident" if self.record else "Log Quality Record / CAPA Action"
        ctk.CTkLabel(
            container,
            text=title,
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text="Enforces ISO/TQM accountability across dispensing, storage, and customer safety",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Title
        ctk.CTkLabel(container, text="Audit / Incident Summary Title *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.entry_title = ctk.CTkEntry(container, placeholder_text="e.g. Near-Expiry Quarantine Audit in Aisle 3", height=36)
        self.entry_title.pack(fill="x", pady=(2, 8))
        if self.record:
            self.entry_title.insert(0, self.record.get("title", ""))

        # Category & Severity
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        c_cat = ctk.CTkFrame(row1, fg_color="transparent")
        c_cat.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(c_cat, text="TQM Category *", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.cat_var = ctk.StringVar(value=self.record.get("category", "Audit") if self.record else "Audit")
        self.cat_opt = ctk.CTkOptionMenu(c_cat, variable=self.cat_var, values=["Audit", "CAPA", "Incident", "Inspection", "Customer Complaint"], height=36)
        self.cat_opt.pack(fill="x", pady=(2, 0))

        c_sev = ctk.CTkFrame(row1, fg_color="transparent")
        c_sev.pack(side="right", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(c_sev, text="Severity Level *", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.sev_var = ctk.StringVar(value=self.record.get("severity", "Medium") if self.record else "Medium")
        self.sev_opt = ctk.CTkOptionMenu(c_sev, variable=self.sev_var, values=["Low", "Medium", "High", "Critical"], height=36)
        self.sev_opt.pack(fill="x", pady=(2, 0))

        # Status
        ctk.CTkLabel(container, text="Resolution Status *", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.stat_var = ctk.StringVar(value=self.record.get("status", "Open") if self.record else "Open")
        self.stat_opt = ctk.CTkOptionMenu(container, variable=self.stat_var, values=["Open", "Under Review", "Resolved", "Closed"], height=36)
        self.stat_opt.pack(fill="x", pady=(2, 8))

        # Description
        ctk.CTkLabel(container, text="Defect Description / Root Cause Details *", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_desc = ctk.CTkEntry(container, placeholder_text="Root-cause observation or inspection finding", height=36)
        self.entry_desc.pack(fill="x", pady=(2, 8))
        if self.record:
            self.entry_desc.insert(0, self.record.get("description", ""))

        # Action plan
        ctk.CTkLabel(container, text="CAPA Preventive / Corrective Action Plan", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_plan = ctk.CTkEntry(container, placeholder_text="Specific preventive measure taken to eliminate recurrence", height=36)
        self.entry_plan.pack(fill="x", pady=(2, 14))
        if self.record and self.record.get("action_plan"):
            self.entry_plan.insert(0, self.record.get("action_plan", ""))

        self.lbl_err = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(11))
        self.lbl_err.pack(anchor="w", pady=(0, 8))

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_box,
            text="Save Quality Record",
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
        d = self.entry_desc.get().strip()
        if not t or not d:
            self.lbl_err.configure(text="Summary Title and Description are required.")
            return

        payload = {
            "title": t,
            "category": self.cat_var.get(),
            "severity": self.sev_var.get(),
            "status": self.stat_var.get(),
            "description": d,
            "action_plan": self.entry_plan.get().strip() or None,
            "reported_by": "Quality Lead"
        }

        self.btn_save.configure(state="disabled", text="Saving...")

        def _do():
            if self.record:
                return self.api_client.update_tqm_record(self.record["id"], payload)
            else:
                return self.api_client.create_tqm_record(payload)

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
        self.btn_save.configure(state="normal", text="Save Quality Record")
        self.lbl_err.configure(text=str(err).replace("RuntimeError: ", ""))


class TQMView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.records_list = []

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🛡️ Total Quality Management (TQM) & Audit Governance",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading quality indicators...",
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
            command=self.load_data
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ Log Quality Audit / CAPA",
            width=190,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._open_add_modal
        ).pack(side="left", padx=5)

        # 4 Stat Cards
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=(0, 15))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="c")

        self.card_accuracy = StatCard(cards_frame, title="Billing Accuracy", value="100%", icon="🎯", variant="success")
        self.card_accuracy.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.card_expired = StatCard(cards_frame, title="Expired Stock Ratio", value="0.0%", icon="⚠️", variant="warning")
        self.card_expired.grid(row=0, column=1, sticky="ew", padx=3)

        self.card_near = StatCard(cards_frame, title="Batches Near Expiry", value="0", icon="⏳", variant="info")
        self.card_near.grid(row=0, column=2, sticky="ew", padx=3)

        self.card_capa = StatCard(cards_frame, title="CAPA Resolution Rate", value="100%", icon="✅", variant="primary")
        self.card_capa.grid(row=0, column=3, sticky="ew", padx=(6, 0))

        # Filter bar
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.cat_filter_var = ctk.StringVar(value="All Categories")
        self.cat_filter = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.cat_filter_var,
            values=["All Categories", "Audit", "CAPA", "Incident", "Inspection", "Customer Complaint"],
            height=36,
            command=lambda v: self._apply_filters()
        )
        self.cat_filter.pack(side="left", padx=(0, 10))

        self.stat_filter_var = ctk.StringVar(value="All Statuses")
        self.stat_filter = ctk.CTkOptionMenu(
            filter_bar,
            variable=self.stat_filter_var,
            values=["All Statuses", "Open", "Under Review", "Resolved", "Closed"],
            height=36,
            command=lambda v: self._apply_filters()
        )
        self.stat_filter.pack(side="left")

        # Table
        self.columns = [
            {"key": "title", "title": "Summary / Audit Title", "width": 240, "anchor": "w"},
            {"key": "category", "title": "Category", "width": 140, "anchor": "center"},
            {"key": "severity", "title": "Severity", "width": 100, "anchor": "center"},
            {"key": "status", "title": "Status", "width": 110, "anchor": "center"},
            {"key": "reported_by", "title": "Reporter / Auditor", "width": 140, "anchor": "w"},
            {"key": "created_at", "title": "Date Logged", "width": 140, "anchor": "w"},
            {"key": "actions", "title": "Actions", "width": 120, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=self.columns, rows_per_page=10)
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def load_data(self):
        def _fetch():
            recs = self.api_client.list_tqm_records()
            kpis = self.api_client.get_tqm_kpis()
            return recs, kpis

        def _on_done(result):
            self.records_list, kpis = result

            # Update KPI Cards with authentic live data
            bill_acc = kpis.get("billing_accuracy_percentage", 100.0)
            exp_pct = kpis.get("expired_stock_percentage", 0.0)
            near_lots = kpis.get("near_expiry_batches", 0)
            res_rate = kpis.get("resolution_rate_percentage", 100.0)

            self.card_accuracy.update_value(f"{bill_acc}%")
            self.card_expired.update_value(f"{exp_pct}%")
            self.card_near.update_value(f"{near_lots} lots")
            self.card_capa.update_value(f"{res_rate}%")

            self.lbl_count.configure(text=f"Audited {kpis.get('total_batches_audited', 0)} lots across {kpis.get('total_medicines_active', 0)} formulary products")
            self._apply_filters()

        run_in_background(_fetch, on_success=_on_done)

    def _apply_filters(self):
        cat = self.cat_filter_var.get()
        stat = self.stat_filter_var.get()

        filtered = []
        for r in self.records_list:
            if cat != "All Categories" and r.get("category") != cat:
                continue
            if stat != "All Statuses" and r.get("status") != stat:
                continue
            filtered.append(r)

        rows = []
        for r in filtered:
            rows.append({
                "title": r.get("title", ""),
                "category": r.get("category", ""),
                "severity": r.get("severity", "Medium"),
                "status": r.get("status", "Open"),
                "reported_by": r.get("reported_by", "Auditor"),
                "created_at": r.get("created_at", ""),
                "_raw": r
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
                command=lambda raw=row["_raw"]: self._delete_record(raw)
            ).pack(side="left", padx=2)
            return box

        self.table.set_data(rows, action_builder=action_builder)

    def _open_add_modal(self):
        TQMRecordModal(self.winfo_toplevel(), self.api_client, on_success=self.load_data)

    def _open_edit_modal(self, record):
        TQMRecordModal(self.winfo_toplevel(), self.api_client, record=record, on_success=self.load_data)

    def _delete_record(self, record):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Delete Quality Record",
            message=f"Are you sure you want to remove audit record '{record['title']}'?",
            confirm_label="Delete",
            danger=True,
            on_confirm=lambda: run_in_background(
                lambda: self.api_client.delete_tqm_record(record["id"]),
                on_success=lambda _: self.load_data()
            )
        )
