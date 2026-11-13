import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.ui.components.stat_card import StatCard
from app.ui.components.data_table import DataTable
from app.client.api_client import APIClient


class CustomerPortalView(ctk.CTkFrame):
    """
    Panel 7: Customer / Patient Portal
    Allows patients to browse available pharmacy formulations, upload doctor prescriptions,
    track review/verification status, view bills & invoices, and contact pharmacy staff.
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
            text="👤 Patient Health & Prescription Portal",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        actions_box = ctk.CTkFrame(header, fg_color="transparent")
        actions_box.pack(side="right")

        ctk.CTkButton(
            actions_box,
            text="📋 Upload New Prescription",
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_upload_modal
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            actions_box,
            text="↻ Refresh",
            width=80,
            font=accessibility_manager.get_font(12),
            fg_color=Theme.BG_MUTED,
            text_color=Theme.TEXT_MAIN,
            command=self.load_data
        ).pack(side="left")

        # 2. KPI Cards
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        for col in range(3):
            self.kpi_frame.grid_columnconfigure(col, weight=1)

        self.card_rx = StatCard(self.kpi_frame, title="Active Prescriptions", value="0", subtitle="On file / under review", icon="📋")
        self.card_rx.grid(row=0, column=0, sticky="nsew", padx=6)

        self.card_orders = StatCard(self.kpi_frame, title="Fulfilled Invoices", value="0", subtitle="Completed pharmacy counter bills", icon="🧾")
        self.card_orders.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_spend = StatCard(self.kpi_frame, title="Total Health Spend", value="₹0.00", subtitle="Cumulative medication purchases", icon="💳")
        self.card_spend.grid(row=0, column=2, sticky="nsew", padx=6)

        # 3. Tab Navigation
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_CARD, corner_radius=12)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.tab_catalog = self.tabview.add("Browse Medicines")
        self.tab_prescriptions = self.tabview.add("My Prescriptions")
        self.tab_invoices = self.tabview.add("Bills & Invoices")
        self.tab_contact = self.tabview.add("Contact Pharmacy")

        self._build_catalog_tab()
        self._build_prescriptions_tab()
        self._build_invoices_tab()
        self._build_contact_tab()

    def _build_catalog_tab(self):
        tab = self.tab_catalog
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        search_bar = ctk.CTkFrame(tab, fg_color="transparent")
        search_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 10))

        ctk.CTkLabel(search_bar, text="Search Pharmacy Formulary:", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left", padx=(0, 8))
        self.txt_catalog_search = ctk.CTkEntry(search_bar, placeholder_text="Enter Brand or Generic Name (e.g. Paracetamol)...", width=320)
        self.txt_catalog_search.pack(side="left", padx=(0, 8))
        self.txt_catalog_search.bind("<Return>", lambda e: self.load_data())

        ctk.CTkButton(
            search_bar,
            text="🔍 Search Catalog",
            width=120,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            command=self.load_data
        ).pack(side="left")

        cols = [
            {"key": "name", "title": "Medicine Trade Name", "width": 200, "anchor": "w"},
            {"key": "generic_name", "title": "Active Ingredient", "width": 180, "anchor": "w"},
            {"key": "category", "title": "Therapeutic Class", "width": 140, "anchor": "w"},
            {"key": "price", "title": "Price / Unit (₹)", "width": 110, "anchor": "e"},
            {"key": "rx_flag", "title": "Prescription Needed?", "width": 130, "anchor": "center"},
            {"key": "stock_status", "title": "Availability", "width": 110, "anchor": "center"},
        ]
        self.tbl_catalog = DataTable(tab, columns=cols)
        self.tbl_catalog.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_prescriptions_tab(self):
        tab = self.tab_prescriptions
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))
        ctk.CTkLabel(toolbar, text="Prescription Verification & Dispensing Status", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")

        cols = [
            {"key": "rx_number", "title": "Rx Number", "width": 120, "anchor": "w"},
            {"key": "doctor_name", "title": "Prescribing Physician", "width": 180, "anchor": "w"},
            {"key": "status", "title": "Pharmacist Status", "width": 130, "anchor": "center"},
            {"key": "dispensing_notes", "title": "Pharmacist Guidance / Notes", "width": 240, "anchor": "w"},
            {"key": "created_at", "title": "Submitted", "width": 130, "anchor": "center"},
        ]
        self.tbl_prescriptions = DataTable(tab, columns=cols)
        self.tbl_prescriptions.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_invoices_tab(self):
        tab = self.tab_invoices
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))
        ctk.CTkLabel(toolbar, text="Past Counter Billing Invoices & Receipts", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")

        cols = [
            {"key": "sale_date", "title": "Invoice Date", "width": 130, "anchor": "center"},
            {"key": "invoice_number", "title": "Invoice Number", "width": 160, "anchor": "w"},
            {"key": "total_amount", "title": "Total Paid (₹)", "width": 120, "anchor": "e"},
            {"key": "payment_method", "title": "Payment Mode", "width": 120, "anchor": "center"},
            {"key": "payment_status", "title": "Payment Status", "width": 110, "anchor": "center"},
            {"key": "items_count", "title": "Items", "width": 80, "anchor": "center"},
        ]
        self.tbl_invoices = DataTable(tab, columns=cols)
        self.tbl_invoices.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_contact_tab(self):
        tab = self.tab_contact
        tab.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(tab, fg_color=Theme.BG_MUTED, corner_radius=10, width=540)
        container.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(container, text="💬 Contact Pharmacy Dispensary / Submit Inquiry", font=accessibility_manager.get_font(15, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 10))

        self.txt_contact_name = self._make_input(container, "Your Name *", "Patient Name")
        self.txt_contact_email = self._make_input(container, "Email Address *", "patient@email.com")
        self.txt_contact_subj = self._make_input(container, "Inquiry Subject *", "Question about dosage / refill")

        ctk.CTkLabel(container, text="Message / Details *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_contact_msg = ctk.CTkTextbox(container, height=90, font=accessibility_manager.get_font(12))
        self.txt_contact_msg.pack(fill="x", padx=20, pady=(0, 10))

        self.lbl_contact_res = ctk.CTkLabel(container, text="", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.SUCCESS_TEXT)
        self.lbl_contact_res.pack(pady=2)

        ctk.CTkButton(
            container,
            text="Transmit Inquiry to Dispensary",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit_contact_ticket
        ).pack(anchor="e", padx=20, pady=(6, 16))

    def _make_input(self, parent, label: str, val: str):
        ctk.CTkLabel(parent, text=label, font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        entry = ctk.CTkEntry(parent, height=32, font=accessibility_manager.get_font(12))
        entry.pack(fill="x", padx=20, pady=(0, 4))
        entry.insert(0, val)
        return entry

    def load_data(self):
        try:
            metrics = self.api_client.get_customer_dashboard()
            self.card_rx.update_value(str(metrics.get("active_prescriptions", 0)))
            self.card_orders.update_value(str(metrics.get("completed_orders", 0)))
            self.card_spend.update_value(f"₹{metrics.get('total_spent', 0):,.2f}")

            # Catalog
            search = self.txt_catalog_search.get().strip() or None
            catalog = self.api_client.get_customer_catalog(search=search)
            catalog_rows = []
            for item in catalog:
                rx_text = "⚠️ YES (Doctor Rx)" if item.get("prescription_required") else "🟢 NO (OTC)"
                stock_text = "🟢 In Stock" if item.get("in_stock") else "🔴 Out of Stock"
                catalog_rows.append({
                    "name": item.get("name"),
                    "generic_name": item.get("generic_name"),
                    "category": item.get("category"),
                    "price": f"₹{item.get('price', 0):.2f}",
                    "rx_flag": rx_text,
                    "stock_status": stock_text
                })
            self.tbl_catalog.set_data(catalog_rows)

            # Prescriptions
            rxs = self.api_client.list_my_prescriptions()
            self.tbl_prescriptions.set_data(rxs)

            # Invoices
            invoices = self.api_client.list_my_orders()
            self.tbl_invoices.set_data(invoices)
        except Exception:
            pass

    def _open_upload_modal(self):
        UploadPrescriptionModal(self.winfo_toplevel(), self.api_client, on_uploaded=self.load_data)

    def _submit_contact_ticket(self):
        name = self.txt_contact_name.get().strip()
        email = self.txt_contact_email.get().strip()
        subj = self.txt_contact_subj.get().strip()
        msg = self.txt_contact_msg.get("1.0", "end").strip()

        if not all([name, email, subj, msg]):
            self.lbl_contact_res.configure(text="Please complete all inquiry fields.", text_color=Theme.DANGER_TEXT)
            return

        try:
            self.api_client.submit_customer_support_ticket({
                "sender_name": name,
                "sender_email": email,
                "subject": subj,
                "message": msg
            })
            self.lbl_contact_res.configure(text="✓ Inquiry submitted successfully. Dispensary staff will follow up.", text_color=Theme.SUCCESS_TEXT)
            self.txt_contact_subj.delete(0, "end")
            self.txt_contact_msg.delete("1.0", "end")
        except Exception as e:
            self.lbl_contact_res.configure(text=str(e)[:45], text_color=Theme.DANGER_TEXT)


class UploadPrescriptionModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, on_uploaded: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.on_uploaded = on_uploaded

        self.title("Upload Doctor Prescription")
        self.geometry("460x420")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="📋 Upload Prescription for Review", font=accessibility_manager.get_font(15, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 6))

        ctk.CTkLabel(container, text="Prescribing Doctor Name *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_doc = ctk.CTkEntry(container, placeholder_text="Dr. Full Name", height=32)
        self.txt_doc.pack(fill="x", padx=20, pady=(0, 6))

        ctk.CTkLabel(container, text="Medical Registration / License #", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_reg = ctk.CTkEntry(container, placeholder_text="MCI-12345 (Optional)", height=32)
        self.txt_reg.pack(fill="x", padx=20, pady=(0, 6))

        ctk.CTkLabel(container, text="Prescribed Medications & Instructions *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_notes = ctk.CTkTextbox(container, height=80, font=accessibility_manager.get_font(12))
        self.txt_notes.pack(fill="x", padx=20, pady=(0, 10))
        self.txt_notes.insert("1.0", "Paracetamol 500mg - 1 tablet three times daily after food")

        self.lbl_err = ctk.CTkLabel(container, text="", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.DANGER_TEXT)
        self.lbl_err.pack(pady=2)

        ctk.CTkButton(
            container,
            text="Submit Prescription to Pharmacist",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=20, pady=(4, 16))

    def _submit(self):
        doc = self.txt_doc.get().strip()
        reg = self.txt_reg.get().strip() or None
        notes = self.txt_notes.get("1.0", "end").strip()

        if not doc or not notes:
            self.lbl_err.configure(text="Doctor name and medications are required.")
            return

        try:
            self.api_client.upload_patient_prescription({
                "doctor_name": doc,
                "doctor_registration": reg,
                "notes": notes
            })
            self.destroy()
            self.on_uploaded()
        except Exception as e:
            self.lbl_err.configure(text=str(e)[:45])
