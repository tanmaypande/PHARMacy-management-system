"""
Patient Prescriptions & Clinical Records View.
"""
from typing import Optional, Dict, Any, List
from datetime import date
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.dialogs import ConfirmDialog
from app.ui.components.data_table import DataTable


class PrescriptionModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.on_success = on_success

        self.title("Record Clinical Prescription")
        self.geometry("480x480")
        self.resizable(False, False)
        self.grab_set()

        self.customers = []
        self.bind("<Escape>", lambda e: self.destroy())
        self._build_form()
        self._load_customers()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        ctk.CTkLabel(
            container,
            text="Record Clinical Prescription",
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text="Links prescription to patient for regulated dispensing compliance",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 12))

        # Patient Dropdown
        ctk.CTkLabel(container, text="Select Patient / Customer *", font=accessibility_manager.get_font(12, weight="bold")).pack(anchor="w")
        self.cust_var = ctk.StringVar(value="Loading patients...")
        self.cust_opt = ctk.CTkOptionMenu(container, variable=self.cust_var, values=["Loading..."], height=36)
        self.cust_opt.pack(fill="x", pady=(2, 8))

        # Doctor Name & License
        row1 = ctk.CTkFrame(container, fg_color="transparent")
        row1.pack(fill="x", pady=(0, 8))

        c_doc = ctk.CTkFrame(row1, fg_color="transparent")
        c_doc.pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkLabel(c_doc, text="Doctor / Prescriber Name *", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_doc = ctk.CTkEntry(c_doc, placeholder_text="e.g. Dr. Rajesh Verma", height=36)
        self.entry_doc.pack(fill="x", pady=(2, 0))

        c_lic = ctk.CTkFrame(row1, fg_color="transparent")
        c_lic.pack(side="right", fill="x", expand=True, padx=(6, 0))
        ctk.CTkLabel(c_lic, text="Medical Reg / License #", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_lic = ctk.CTkEntry(c_lic, placeholder_text="e.g. MCI-29381", height=36)
        self.entry_lic.pack(fill="x", pady=(2, 0))

        # Diagnosis
        ctk.CTkLabel(container, text="Clinical Diagnosis / Indication", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_diag = ctk.CTkEntry(container, placeholder_text="e.g. Acute Bronchitis, Type 2 Diabetes", height=36)
        self.entry_diag.pack(fill="x", pady=(2, 8))

        # Notes
        ctk.CTkLabel(container, text="Dosage & Administration Notes", font=accessibility_manager.get_font(12)).pack(anchor="w")
        self.entry_notes = ctk.CTkEntry(container, placeholder_text="e.g. 1 tab twice daily after meals for 5 days", height=36)
        self.entry_notes.pack(fill="x", pady=(2, 14))

        self.lbl_err = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(11))
        self.lbl_err.pack(anchor="w", pady=(0, 8))

        btn_box = ctk.CTkFrame(container, fg_color="transparent")
        btn_box.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_box,
            text="Save Prescription",
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

    def _load_customers(self):
        def _fetch():
            return self.api_client.list_customers()

        def _on_done(custs):
            self.customers = custs or []
            if self.customers:
                names = [f"{c['name']} ({c.get('phone') or 'No phone'})" for c in self.customers]
                self.cust_opt.configure(values=names)
                self.cust_var.set(names[0])
            else:
                self.cust_opt.configure(values=["No patients registered - Enroll patient first"])
                self.cust_var.set("No patients registered - Enroll patient first")

        run_in_background(_fetch, on_success=_on_done)

    def _save(self):
        sel_c_str = self.cust_var.get()
        if not self.customers or "No patients" in sel_c_str:
            self.lbl_err.configure(text="Please enroll a patient first.")
            return

        c_idx = self.cust_opt.cget("values").index(sel_c_str)
        cust = self.customers[c_idx]

        doc = self.entry_doc.get().strip()
        if not doc:
            self.lbl_err.configure(text="Doctor name is required.")
            return

        payload = {
            "customer_id": cust["id"],
            "doctor_name": doc,
            "doctor_license": self.entry_lic.get().strip() or None,
            "prescription_date": date.today().strftime("%Y-%m-%d"),
            "diagnosis": self.entry_diag.get().strip() or None,
            "notes": self.entry_notes.get().strip() or None
        }

        self.btn_save.configure(state="disabled", text="Saving...")

        def _do():
            return self.api_client.create_prescription(payload)

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
        self.btn_save.configure(state="normal", text="Save Prescription")
        self.lbl_err.configure(text=str(err).replace("RuntimeError: ", ""))


class PrescriptionView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.prescriptions_list = []

        self._build_ui()
        self.load_prescriptions()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📋 Patient Prescriptions & Clinical Records",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading prescriptions...",
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
            command=self.load_prescriptions
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ New Prescription",
            width=160,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self._open_add_modal
        ).pack(side="left", padx=5)

        # Table
        self.columns = [
            {"key": "patient", "title": "Patient Name", "width": 220, "anchor": "w"},
            {"key": "doctor", "title": "Prescribing Doctor", "width": 200, "anchor": "w"},
            {"key": "date", "title": "Prescription Date", "width": 140, "anchor": "w"},
            {"key": "diagnosis", "title": "Diagnosis", "width": 220, "anchor": "w"},
            {"key": "notes", "title": "Dosage Notes", "width": 240, "anchor": "w"},
            {"key": "actions", "title": "Actions", "width": 100, "anchor": "center"},
        ]
        self.table = DataTable(self, columns=self.columns, rows_per_page=12)
        self.table.pack(fill="both", expand=True, padx=20, pady=(10, 15))

    def load_prescriptions(self):
        self.lbl_count.configure(text="Fetching clinical prescriptions...")
        run_in_background(
            lambda: self.api_client.list_prescriptions(),
            on_success=self._on_loaded,
            on_error=lambda err: self.lbl_count.configure(text=f"Error: {err}")
        )

    def _on_loaded(self, prescriptions):
        self.prescriptions_list = prescriptions or []
        self.lbl_count.configure(text=f"Total: {len(self.prescriptions_list)} clinical records on file")
        rows = []
        for p in self.prescriptions_list:
            rows.append({
                "patient": p.get("customer_name", "—"),
                "doctor": f"Dr. {p.get('doctor_name', '—')}",
                "date": p.get("prescription_date", ""),
                "diagnosis": p.get("diagnosis") or "—",
                "notes": p.get("notes") or "—",
                "_raw": p
            })

        def action_builder(parent, row):
            box = ctk.CTkFrame(parent, fg_color="transparent")
            ctk.CTkButton(
                box,
                text="🗑️",
                width=32,
                height=26,
                fg_color=Theme.DANGER_BG,
                text_color=Theme.DANGER_TEXT,
                command=lambda raw=row["_raw"]: self._delete_prescription(raw)
            ).pack(side="left", padx=2)
            return box

        self.table.set_data(rows, action_builder=action_builder)

    def _open_add_modal(self):
        PrescriptionModal(self.winfo_toplevel(), self.api_client, on_success=self.load_prescriptions)

    def _delete_prescription(self, p):
        ConfirmDialog(
            self.winfo_toplevel(),
            title="Delete Prescription",
            message=f"Are you sure you want to delete prescription record for '{p['customer_name']}'?",
            confirm_label="Delete",
            danger=True,
            on_confirm=lambda: run_in_background(
                lambda: self.api_client.delete_prescription(p["id"]),
                on_success=lambda _: self.load_prescriptions()
            )
        )
