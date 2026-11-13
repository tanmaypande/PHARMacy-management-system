import customtkinter as ctk
from typing import Dict, Any, List, Optional, Callable
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.ui.components.stat_card import StatCard
from app.ui.components.data_table import DataTable
from app.client.api_client import APIClient


class SuperAdminView(ctk.CTkFrame):
    """
    Panel 1: Super Admin Panel
    Software owner controlling all registered pharmacies, licenses,
    global subscriptions, support tickets, and system-wide audit logs.
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
            text="👑 Super Administrator Control Center",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="+ Onboard New Pharmacy",
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_register_modal
        ).pack(side="right")

        # 2. KPI Cards
        self.kpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.kpi_frame.grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 16))
        for col in range(4):
            self.kpi_frame.grid_columnconfigure(col, weight=1)

        self.card_total_p = StatCard(self.kpi_frame, title="Total Pharmacies", value="0", subtitle="Registered tenants", icon="🏥")
        self.card_total_p.grid(row=0, column=0, sticky="nsew", padx=6)

        self.card_active_p = StatCard(self.kpi_frame, title="Active Licenses", value="0", subtitle="Compliant & active", icon="✅")
        self.card_active_p.grid(row=0, column=1, sticky="nsew", padx=6)

        self.card_users = StatCard(self.kpi_frame, title="Platform Users", value="0", subtitle="Across all tenants", icon="👥")
        self.card_users.grid(row=0, column=2, sticky="nsew", padx=6)

        self.card_tickets = StatCard(self.kpi_frame, title="Open Support", value="0", subtitle="Pending resolution", icon="🎫")
        self.card_tickets.grid(row=0, column=3, sticky="nsew", padx=6)

        # 3. Tab Navigation (Pharmacies, Subscriptions, Support Tickets, Audit Trail)
        self.tabview = ctk.CTkTabview(self, fg_color=Theme.BG_CARD, corner_radius=12)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20))

        self.tab_pharmacies = self.tabview.add("Registered Pharmacies")
        self.tab_subs = self.tabview.add("Subscriptions & Plans")
        self.tab_tickets = self.tabview.add("Support Tickets")
        self.tab_audit = self.tabview.add("System-Wide Audit Trail")

        self._build_pharmacies_tab()
        self._build_subs_tab()
        self._build_tickets_tab()
        self._build_audit_tab()

    def _build_pharmacies_tab(self):
        tab = self.tab_pharmacies
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))

        ctk.CTkLabel(toolbar, text="Multi-Tenant Pharmacy Directory", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")

        ctk.CTkButton(
            toolbar,
            text="↻ Refresh",
            width=80,
            height=28,
            fg_color=Theme.BG_MUTED,
            text_color=Theme.TEXT_MAIN,
            command=self.load_data
        ).pack(side="right")

        cols = [
            {"key": "name", "title": "Dispensary Trade Name", "width": 190, "anchor": "w"},
            {"key": "license_number", "title": "Drug License No", "width": 140, "anchor": "w"},
            {"key": "owner_name", "title": "Proprietor", "width": 140, "anchor": "w"},
            {"key": "phone", "title": "Contact Phone", "width": 120, "anchor": "w"},
            {"key": "status", "title": "Status", "width": 90, "anchor": "center"},
            {"key": "subscription_plan", "title": "Plan Tier", "width": 100, "anchor": "center"},
            {"key": "created_at", "title": "Onboarded", "width": 100, "anchor": "center"},
        ]

        self.tbl_pharmacies = DataTable(
            tab,
            columns=cols,
            on_action_click=self._on_pharmacy_action,
            action_button_text="Toggle Status"
        )
        self.tbl_pharmacies.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_subs_tab(self):
        tab = self.tab_subs
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        cols = [
            {"key": "pharmacy_name", "title": "Pharmacy Name", "width": 200, "anchor": "w"},
            {"key": "plan_name", "title": "License Plan", "width": 140, "anchor": "w"},
            {"key": "status", "title": "Subscription Status", "width": 120, "anchor": "center"},
            {"key": "price", "title": "Annual Fee ($)", "width": 110, "anchor": "e"},
            {"key": "start_date", "title": "Valid From", "width": 110, "anchor": "center"},
            {"key": "end_date", "title": "Renews / Expires", "width": 110, "anchor": "center"},
        ]
        self.tbl_subs = DataTable(tab, columns=cols)
        self.tbl_subs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def _build_tickets_tab(self):
        tab = self.tab_tickets
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        toolbar = ctk.CTkFrame(tab, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 10))
        ctk.CTkLabel(toolbar, text="Inbound Support Tickets & Inquiries", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(side="left")

        cols = [
            {"key": "ticket_number", "title": "Ticket #", "width": 100, "anchor": "w"},
            {"key": "pharmacy_name", "title": "Tenant / Sender", "width": 150, "anchor": "w"},
            {"key": "subject", "title": "Subject", "width": 200, "anchor": "w"},
            {"key": "priority", "title": "Priority", "width": 80, "anchor": "center"},
            {"key": "status", "title": "Status", "width": 90, "anchor": "center"},
            {"key": "created_at", "title": "Received", "width": 120, "anchor": "center"},
        ]
        self.tbl_tickets = DataTable(
            tab,
            columns=cols,
            on_action_click=self._on_ticket_action,
            action_button_text="Reply"
        )
        self.tbl_tickets.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_audit_tab(self):
        tab = self.tab_audit
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        cols = [
            {"key": "timestamp", "title": "Timestamp (UTC)", "width": 150, "anchor": "w"},
            {"key": "username", "title": "Actor", "width": 120, "anchor": "w"},
            {"key": "action", "title": "Security Action", "width": 150, "anchor": "w"},
            {"key": "entity_type", "title": "Entity", "width": 110, "anchor": "w"},
            {"key": "details", "title": "Audit Event Log", "width": 300, "anchor": "w"},
        ]
        self.tbl_audit = DataTable(tab, columns=cols)
        self.tbl_audit.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    def load_data(self):
        try:
            metrics = self.api_client.get_super_admin_dashboard()
            self.card_total_p.update_value(str(metrics.get("total_registered_pharmacies", 0)))
            self.card_active_p.update_value(str(metrics.get("active_pharmacies", 0)))
            self.card_users.update_value(str(metrics.get("total_system_users", 0)))
            self.card_tickets.update_value(str(metrics.get("pending_support_tickets", 0)))

            pharmacies = self.api_client.list_pharmacies()
            self.tbl_pharmacies.set_data(pharmacies)

            subs = self.api_client.list_subscriptions()
            self.tbl_subs.set_data(subs)

            tickets = self.api_client.list_support_tickets()
            self.tbl_tickets.set_data(tickets)

            logs = self.api_client.get_super_admin_audit_logs()
            self.tbl_audit.set_data(logs)
        except Exception:
            pass

    def _on_pharmacy_action(self, row: Dict[str, Any]):
        p_id = row.get("id")
        if p_id:
            try:
                self.api_client.toggle_pharmacy_status(p_id)
                self.load_data()
            except Exception:
                pass

    def _on_ticket_action(self, row: Dict[str, Any]):
        t_id = row.get("id")
        if t_id:
            ReplyTicketModal(self.winfo_toplevel(), self.api_client, row, on_replied=self.load_data)

    def _open_register_modal(self):
        RegisterPharmacyModal(self.winfo_toplevel(), self.api_client, on_registered=self.load_data)


class RegisterPharmacyModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, on_registered: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.on_registered = on_registered

        self.title("Onboard New Pharmacy Tenant")
        self.geometry("500x620")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="🏥 Register Pharmacy Tenant", font=accessibility_manager.get_font(16, weight="bold"), text_color=Theme.TEXT_MAIN).pack(pady=(16, 10))

        self.txt_name = self._make_field(container, "Dispensary Name *", "MediCare Pharmacy")
        self.txt_lic = self._make_field(container, "Drug License Number *", "DL-2026-STATE-09")
        self.txt_owner = self._make_field(container, "Proprietor / Owner Name *", "Dr. Rajesh Varma")
        self.txt_phone = self._make_field(container, "Registered Phone *", "+91 98765 43210")
        self.txt_email = self._make_field(container, "Correspondence Email *", "owner@pharmacy.com")
        self.txt_user = self._make_field(container, "Owner Username *", "pharmacy_owner")
        self.txt_pwd = self._make_field(container, "Owner Password *", "Secure password", show="●")

        self.lbl_err = ctk.CTkLabel(container, text="", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.DANGER_TEXT)
        self.lbl_err.pack(pady=4)

        ctk.CTkButton(
            container,
            text="Confirm & Provision Pharmacy",
            height=38,
            font=accessibility_manager.get_font(13, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        ).pack(fill="x", padx=30, pady=(8, 16))

    def _make_field(self, parent, label: str, placeholder: str, show: Optional[str] = None):
        ctk.CTkLabel(parent, text=label, font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=30, pady=(3, 1))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=30, show=show, font=accessibility_manager.get_font(12))
        entry.pack(fill="x", padx=30, pady=(0, 2))
        return entry

    def _submit(self):
        name = self.txt_name.get().strip()
        lic = self.txt_lic.get().strip()
        owner = self.txt_owner.get().strip()
        phone = self.txt_phone.get().strip()
        email = self.txt_email.get().strip()
        u = self.txt_user.get().strip()
        p = self.txt_pwd.get().strip()

        if not all([name, lic, owner, phone, email, u, p]):
            self.lbl_err.configure(text="All required fields must be completed.")
            return

        try:
            self.api_client.register_pharmacy({
                "name": name,
                "license_number": lic,
                "owner_name": owner,
                "phone": phone,
                "email": email,
                "address": "Registered Dispensary",
                "subscription_plan": "Enterprise",
                "owner_username": u,
                "owner_password": p
            })
            self.destroy()
            self.on_registered()
        except Exception as e:
            self.lbl_err.configure(text=str(e)[:45])


class ReplyTicketModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, ticket_data: Dict[str, Any], on_replied: Callable[[], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.ticket_data = ticket_data
        self.on_replied = on_replied

        self.title(f"Reply to Support Ticket: {ticket_data.get('ticket_number')}")
        self.geometry("480x420")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text=f"🎫 {self.ticket_data.get('ticket_number')} — {self.ticket_data.get('subject')}", font=accessibility_manager.get_font(14, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(16, 6))

        # Message preview
        msg_box = ctk.CTkTextbox(container, height=90, font=accessibility_manager.get_font(12), fg_color=Theme.BG_MUTED)
        msg_box.pack(fill="x", padx=20, pady=(0, 10))
        msg_box.insert("1.0", f"Sender: {self.ticket_data.get('sender_name')} ({self.ticket_data.get('sender_email')})\n\n{self.ticket_data.get('message')}")
        msg_box.configure(state="disabled")

        ctk.CTkLabel(container, text="Resolution / Administrator Response *", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=20, pady=(4, 2))
        self.txt_response = ctk.CTkTextbox(container, height=90, font=accessibility_manager.get_font(12))
        self.txt_response.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            container,
            text="Send Response & Mark Resolved",
            height=36,
            font=accessibility_manager.get_font(12, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._send_reply
        ).pack(fill="x", padx=20, pady=(4, 16))

    def _send_reply(self):
        resp_text = self.txt_response.get("1.0", "end").strip()
        if not resp_text:
            return
        t_id = self.ticket_data.get("id")
        try:
            self.api_client.reply_support_ticket(t_id, resp_text, "Resolved")
            self.destroy()
            self.on_replied()
        except Exception:
            pass
