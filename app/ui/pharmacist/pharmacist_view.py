import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.ui.components.stat_card import StatCard
from app.ui.components.data_table import DataTable
from app.client.api_client import APIClient


class PharmacistView(ctk.CTkFrame):
    """
    Panel 3: Pharmacist Clinical & Dispensing Panel
    Safe medicine dispensing, clinical prescription review, dosage checks,
    contraindication alerts, and patient medication profile lookup.
    """
    def __init__(self, parent, api_client: APIClient):
        super().__init__(parent, fg_color=Theme.BG_APP)
        self.api_client = api_client

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header Banner
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 12))

        ctk.CTkLabel(
            header,
            text="💊 Registered Pharmacist — Clinical Review & Dispensing",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="↻ Refresh Queue",
            width=110,
            font=accessibility_manager.get_font(12),
            fg_color=Theme.BG_MUTED,
            text_color=Theme.TEXT_MAIN,
            command=self.load_data
        ).pack(side="right")

        # 2. KPI Cards
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        for col in range(4):
            self.kpi_frame.grid_columnconfigure(col, weight=1)

        self.card_pending = StatCard(self.kpi_frame, title="Pending Verification", value="0", subtitle="Requires pharmacist review", icon="📋")
        self.card_pending.grid(row=0, column=0, sticky="nsew", padx=6)

        self.card_verified = StatCard(self.kpi_frame, title="Verified for Dispensing", value="0", subtitle="Ready at counter", icon="✅")
        self.card_verified.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_dispensed = StatCard(self.kpi_frame, title="Dispensed Today", value="0", subtitle="Safely fulfilled", icon="💊")
        self.card_dispensed.grid(row=0, column=2, sticky="nsew", padx=6)

        self.card_expiry = StatCard(self.kpi_frame, title="Near Expiry Batches", value="0", subtitle="Expiring within 30 days", icon="⚠️")
        self.card_expiry.grid(row=0, column=3, sticky="nsew", padx=6)

        # 3. Tab Navigation
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_CARD, corner_radius=12)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.tab_queue = self.tabview.add("Prescriptions Review Queue")
        self.tab_history = self.tabview.add("Patient Medication Profiles")
        self.tab_batches = self.tabview.add("Formulary Batches & Expiry")

        self._build_queue_tab()
        self._build_history_tab()
        self._build_batches_tab()

    def _build_queue_tab(self):
        tab = self.tab_queue
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))

        ctk.CTkLabel(toolbar, text="Filter by Clinical Status:", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=(0, 8))
        self.cmb_status_filter = ctk.CTkComboBox(toolbar, values=["All", "Pending", "Verified", "Dispensed", "Rejected"], width=130, command=lambda v: self.load_data())
        self.cmb_status_filter.pack(side="left")

        actions_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="✓ Verify Selected Rx",
            font=accessibility_manager.get_font(11, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._on_verify_click
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="✕ Reject Rx",
            font=accessibility_manager.get_font(11, weight="bold"),
            fg_color=Theme.DANGER,
            hover_color=Theme.DANGER_HOVER,
            command=self._on_reject_click
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            actions_box,
            text="💊 Dispense",
            font=accessibility_manager.get_font(11, weight="bold"),
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MAIN,
            command=self._on_dispense_click
        ).pack(side="left", padx=4)

        cols = [
            {"key": "rx_number", "title": "Rx Number", "width": 110, "anchor": "w"},
            {"key": "patient_name", "title": "Patient Name", "width": 160, "anchor": "w"},
            {"key": "doctor_name", "title": "Prescribing Physician", "width": 150, "anchor": "w"},
            {"key": "doctor_registration", "title": "Medical Reg #", "width": 110, "anchor": "w"},
            {"key": "status", "title": "Clinical Status", "width": 100, "anchor": "center"},
            {"key": "notes", "title": "Rx Notes / Medications", "width": 200, "anchor": "w"},
            {"key": "dispensing_notes", "title": "Pharmacist Notes", "width": 180, "anchor": "w"},
            {"key": "created_at", "title": "Prescribed Date", "width": 110, "anchor": "center"},
        ]
        self.tbl_queue = DataTable(tab, columns=cols, on_row_select=self._on_select_rx)
        self.tbl_queue.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.selected_rx = None

    def _build_history_tab(self):
        tab = self.tab_history
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        search_bar = ctk.CTkFrame(tab, fg_color="transparent")
        search_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 10))

        ctk.CTkLabel(search_bar, text="Search Patient Medication Record:", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=(0, 8))
        self.txt_patient_search = ctk.CTkEntry(search_bar, placeholder_text="Enter Patient Name or ID...", width=260)
        self.txt_patient_search.pack(side="left", padx=(0, 8))
        self.txt_patient_search.bind("<Return>", lambda e: self._search_patient_history())

        ctk.CTkButton(
            search_bar,
            text="🔍 Search Profile",
            width=110,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=self._search_patient_history
        ).pack(side="left")

        cols = [
            {"key": "date", "title": "Dispensed Date", "width": 110, "anchor": "center"},
            {"key": "invoice_number", "title": "Bill Reference #", "width": 130, "anchor": "w"},
            {"key": "medicine_name", "title": "Pharmaceutical Item", "width": 220, "anchor": "w"},
            {"key": "batch_number", "title": "Batch / Lot", "width": 120, "anchor": "w"},
            {"key": "quantity", "title": "Dispensed Qty", "width": 100, "anchor": "e"},
            {"key": "payment_status", "title": "Fulfillment", "width": 110, "anchor": "center"},
        ]
        self.tbl_history = DataTable(tab, columns=cols)
        self.tbl_history.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_batches_tab(self):
        tab = self.tab_batches
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        cols = [
            {"key": "medicine_name", "title": "Medicine Formulation", "width": 220, "anchor": "w"},
            {"key": "batch_number", "title": "Lot Number", "width": 130, "anchor": "w"},
            {"key": "current_stock", "title": "Units Available", "width": 110, "anchor": "e"},
            {"key": "expiry_date", "title": "Expiration Date", "width": 110, "anchor": "center"},
            {"key": "status", "title": "Safety Alert", "width": 120, "anchor": "center"},
        ]
        self.tbl_batches = DataTable(tab, columns=cols)
        self.tbl_batches.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def load_data(self):
        try:
            metrics = self.api_client.get_pharmacist_dashboard()
            self.card_pending.update_value(str(metrics.get("pending_prescriptions", 0)))
            self.card_verified.update_value(str(metrics.get("verified_prescriptions", 0)))
            self.card_dispensed.update_value(str(metrics.get("dispensed_prescriptions", 0)))
            self.card_expiry.update_value(str(metrics.get("near_expiry_batches", 0)))

            status_f = self.cmb_status_filter.get()
            rxs = self.api_client.list_pharmacist_prescriptions(status=status_f)
            self.tbl_queue.set_data(rxs)

            batches = self.api_client.list_batches()
            batch_rows = []
            for b in batches:
                is_exp = b.get("is_expired", False)
                days = b.get("days_until_expiry", 999)
                alert = "🔴 EXPIRED" if is_exp else ("🟡 NEAR EXPIRY" if days <= 30 else "🟢 SAFE")
                batch_rows.append({
                    "medicine_name": b.get("medicine_name") or "Drug",
                    "batch_number": b.get("batch_number") or "",
                    "current_stock": b.get("quantity", 0),
                    "expiry_date": str(b.get("expiry_date", "")),
                    "status": alert
                })
            self.tbl_batches.set_data(batch_rows)
        except Exception:
            pass

    def _on_select_rx(self, row: Dict[str, Any]):
        self.selected_rx = row

    def _on_verify_click(self):
        if not self.selected_rx:
            return
        VerifyPrescriptionModal(self.winfo_toplevel(), self.api_client, self.selected_rx, on_done=self.load_data)

    def _on_reject_click(self):
        if not self.selected_rx:
            return
        RejectPrescriptionModal(self.winfo_toplevel(), self.api_client, self.selected_rx, on_done=self.load_data)

    def _on_dispense_click(self):
        if not self.selected_rx:
            return
        rx_id = self.selected_rx.get("id")
        try:
            self.api_client.dispense_prescription(rx_id)
            self.load_data()
        except Exception:
            pass

    def _search_patient_history(self):
        cust_query = self.txt_patient_search.get().strip()
        if not cust_query:
            return
        try:
            customers = self.api_client.list_customers()
            target_id = None
            for c in customers:
                if cust_query.lower() in c.get("name", "").lower() or cust_query in str(c.get("phone", "")):
                    target_id = c.get("id")
                    break
            if target_id:
                history = self.api_client.get_patient_medication_history(target_id)
                self.tbl_history.set_data(history)
            else:
                self.tbl_history.set_data([])
        except Exception:
            pass


class VerifyPrescriptionModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, rx_data: Dict[str, Any], on_done: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.rx_data = rx_data
        self.on_done = on_done

        self.title("Verify Clinical Prescription")
        self.geometry("460x380")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"📋 Verify Rx: {self.rx_data.get('rx_number')}", font=accessibility_manager.get_font(15, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 6))

        info_text = f"Patient: {self.rx_data.get('patient_name')}\nDoctor: {self.rx_data.get('doctor_name')} ({self.rx_data.get('doctor_registration') or 'Reg N/A'})\nPrescribed: {self.rx_data.get('notes')}"
        info_box = ctk.CTkTextbox(container, height=80, font=accessibility_manager.get_font(12), fg_color=Theme.BG_MUTED)
        info_box.pack(fill="x", padx=20, pady=(0, 10))
        info_box.insert("1.0", info_text)
        info_box.configure(state="disabled")

        ctk.CTkLabel(container, text="Pharmacist Verification & Dispensing Instructions *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_notes = ctk.CTkTextbox(container, height=70, font=accessibility_manager.get_font(12))
        self.txt_notes.pack(fill="x", padx=20, pady=(0, 12))
        self.txt_notes.insert("1.0", "Verified for therapeutic dosage and lack of contraindications.")

        ctk.CTkButton(
            container,
            text="✓ Approve & Authorize Dispensing",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=20, pady=(4, 16))

    def _submit(self):
        notes = self.txt_notes.get("1.0", "end").strip()
        rx_id = self.rx_data.get("id")
        try:
            self.api_client.verify_prescription(rx_id, notes)
            self.destroy()
            self.on_done()
        except Exception:
            pass


class RejectPrescriptionModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, rx_data: Dict[str, Any], on_done: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.rx_data = rx_data
        self.on_done = on_done

        self.title("Reject Prescription")
        self.geometry("440x300")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"✕ Reject Rx: {self.rx_data.get('rx_number')}", font=accessibility_manager.get_font(15, weight="bold"), text_color=Theme.DANGER_TEXT).pack(anchor="w", padx=20, pady=(16, 8))

        ctk.CTkLabel(container, text="Clinical Rejection Reason *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_reason = ctk.CTkTextbox(container, height=80, font=accessibility_manager.get_font(12))
        self.txt_reason.pack(fill="x", padx=20, pady=(0, 12))
        self.txt_reason.insert("1.0", "Illegible dosage instructions / suspected contraindication.")

        ctk.CTkButton(
            container,
            text="Confirm Rejection",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.DANGER,
            hover_color=Theme.DANGER_HOVER,
            command=self._submit
        ).pack(fill="x", padx=20, pady=(4, 16))

    def _submit(self):
        reason = self.txt_reason.get("1.0", "end").strip()
        rx_id = self.rx_data.get("id")
        try:
            self.api_client.reject_prescription(rx_id, reason)
            self.destroy()
            self.on_done()
        except Exception:
            pass
