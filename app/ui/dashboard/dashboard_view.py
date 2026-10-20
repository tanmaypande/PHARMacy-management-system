import threading
from datetime import date
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.stat_card import StatCard
from app.ui.components.badge import StatusBadge
from app.ui.components.empty_state import EmptyState


class DashboardView(ctk.CTkFrame):
    """
    Healthcare SaaS Operational Dashboard.
    Provides real-time clinical KPIs and TQM quality risk monitoring directly from PostgreSQL.
    """
    def __init__(self, master, api_client: APIClient, on_navigate=None):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.on_navigate = on_navigate

        self._build_ui()
        self.refresh_metrics()

    def _build_ui(self):
        # Top Action Bar
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(action_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Clinical Operations & Quality Monitoring",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Real-time pharmaceutical inventory, compliance metrics, and safety alerts",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        btn_row = ctk.CTkFrame(action_bar, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=100,
            height=36,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(12, weight="bold"),
            command=self.refresh_metrics
        ).pack(side="left", padx=5)

        # Primary KPI Cards Row (4 Columns)
        kpi_row = ctk.CTkFrame(self, fg_color="transparent")
        kpi_row.pack(fill="x", padx=16, pady=(5, 10))
        kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_meds = StatCard(kpi_row, "Medicines Catalog", "...", "Active Master Items", "💊")
        self.card_meds.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.card_cats = StatCard(kpi_row, "Drug Categories", "...", "Classification Groups", "🗂")
        self.card_cats.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        self.card_batches = StatCard(kpi_row, "Active Batches", "...", "Receiving Lots", "📦")
        self.card_batches.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

        self.card_stock = StatCard(kpi_row, "Physical Stock Units", "...", "Total Units On-Hand", "🔢")
        self.card_stock.grid(row=0, column=3, padx=6, pady=6, sticky="nsew")

        # TQM Risk Monitoring Cards Row (3 Columns)
        tqm_row = ctk.CTkFrame(self, fg_color="transparent")
        tqm_row.pack(fill="x", padx=16, pady=(0, 15))
        tqm_row.grid_columnconfigure((0, 1, 2), weight=1)

        self.card_low_stock = StatCard(tqm_row, "Low Stock Warning", "...", "Below Reorder Level", "⚠️")
        self.card_low_stock.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.card_expiring = StatCard(tqm_row, "Expiring Soon", "...", "Due within 30 Days", "⏳")
        self.card_expiring.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        self.card_expired = StatCard(tqm_row, "Expired Lots Blocked", "...", "Isolated from POS", "🛑")
        self.card_expired.grid(row=0, column=2, padx=6, pady=6, sticky="nsew")

        # Lower Split Layout: Critical Expiry Monitoring & Quick Actions
        lower_frame = ctk.CTkFrame(self, fg_color="transparent")
        lower_frame.pack(fill="both", expand=True, padx=22, pady=(0, 15))
        lower_frame.grid_columnconfigure(0, weight=3)
        lower_frame.grid_columnconfigure(1, weight=2)
        lower_frame.grid_rowconfigure(0, weight=1)

        # Left Container: Expiring Batches Table
        self.alerts_box = ctk.CTkFrame(lower_frame, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        self.alerts_box.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        alerts_hdr = ctk.CTkFrame(self.alerts_box, fg_color="transparent")
        alerts_hdr.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            alerts_hdr,
            text="⚠️ Critical Quality & Expiry Monitoring",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        if self.on_navigate:
            ctk.CTkButton(
                alerts_hdr,
                text="View All Batches →",
                width=120,
                height=28,
                fg_color="transparent",
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.PRIMARY,
                font=accessibility_manager.get_font(12, weight="bold"),
                command=lambda: self.on_navigate("inventory")
            ).pack(side="right")

        self.alerts_scroll = ctk.CTkScrollableFrame(self.alerts_box, fg_color="transparent")
        self.alerts_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Right Container: Operational Shortcuts & System Safeguards
        right_panel = ctk.CTkFrame(lower_frame, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        right_panel.grid(row=0, column=1, padx=(10, 0), sticky="nsew")

        ctk.CTkLabel(
            right_panel,
            text="⚡ Clinical Shortcuts",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=16, pady=(14, 12))

        if self.on_navigate:
            # Action 1
            ctk.CTkButton(
                right_panel,
                text="➕  Register New Medicine",
                height=40,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                font=accessibility_manager.get_font(13, weight="bold"),
                command=lambda: self.on_navigate("medicines")
            ).pack(fill="x", padx=16, pady=4)

            # Action 2
            ctk.CTkButton(
                right_panel,
                text="📦  Receive Inventory Batch",
                height=40,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                font=accessibility_manager.get_font(13, weight="bold"),
                command=lambda: self.on_navigate("inventory")
            ).pack(fill="x", padx=16, pady=4)

            # Action 3
            ctk.CTkButton(
                right_panel,
                text="🗂  Manage Drug Categories",
                height=40,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                font=accessibility_manager.get_font(13, weight="bold"),
                command=lambda: self.on_navigate("categories")
            ).pack(fill="x", padx=16, pady=4)

        # Architectural Guard Note
        guard_box = ctk.CTkFrame(right_panel, fg_color=Theme.BG_MUTED, corner_radius=8)
        guard_box.pack(fill="x", padx=16, pady=(16, 16))

        ctk.CTkLabel(
            guard_box,
            text="🛡️ TQM System Controls Active",
            font=accessibility_manager.get_font(12, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=12, pady=(10, 2))

        ctk.CTkLabel(
            guard_box,
            text="• Direct DB connections blocked from UI client\n"
                 "• Poka-Yoke expired batch prevention enabled\n"
                 "• Non-negative inventory check constraint active\n"
                 "• PostgreSQL 18 transactional integrity verified",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED,
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 10))

    def refresh_metrics(self):
        def _fetch():
            try:
                metrics = self.api_client.get_dashboard_metrics()
                expiring = self.api_client.list_expiring_soon(days=30)
                self.after(0, self._render_metrics, metrics, expiring)
            except Exception as exc:
                self.after(0, self._render_error, str(exc))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_metrics(self, m: dict, expiring: list):
        self.card_meds.update_value(m.get("active_medicines", 0), f"Out of {m.get('total_medicines', 0)} total")
        self.card_cats.update_value(m.get("total_categories", 0), "Clinical Classes")
        self.card_batches.update_value(m.get("total_batches", 0), "Active Shipments")
        self.card_stock.update_value(m.get("total_stock_units", 0), "Available in Stock")

        low_stock = m.get("low_stock_medicines", 0)
        self.card_low_stock.update_value(
            low_stock,
            "Urgent Action Needed" if low_stock > 0 else "All Stock Levels Good"
        )

        exp_soon = m.get("expiring_soon_batches", 0)
        self.card_expiring.update_value(
            exp_soon,
            "Due for Review" if exp_soon > 0 else "No Near-Term Expiry"
        )

        expired = m.get("expired_batches", 0)
        self.card_expired.update_value(
            expired,
            "Quarantined from Sales" if expired > 0 else "Zero Expired Stock"
        )

        # Populate Expiring Batches Table
        for widget in self.alerts_scroll.winfo_children():
            widget.destroy()

        if not expiring:
            EmptyState(
                self.alerts_scroll,
                icon="✅",
                title="Zero Expiry Alerts",
                description="No pharmaceutical batches are expiring within the next 30 days."
            ).pack(fill="both", expand=True, pady=10)
            return

        # Mini Table Header
        hdr = ctk.CTkFrame(self.alerts_scroll, fg_color=Theme.BG_MUTED, height=32, corner_radius=6)
        hdr.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(hdr, text="Batch #", width=100, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Medicine", width=160, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Units", width=60, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)
        ctk.CTkLabel(hdr, text="Status", width=120, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=8)

        for b in expiring[:6]:  # Show top 6 alerts
            row = ctk.CTkFrame(self.alerts_scroll, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(row, text=b["batch_number"], width=100, anchor="w", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.PRIMARY).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=b.get("medicine_name") or "—", width=160, anchor="w", font=accessibility_manager.get_font(12), text_color=Theme.TEXT_MAIN).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=str(b["quantity"]), width=60, anchor="center", font=accessibility_manager.get_font(12), text_color=Theme.TEXT_MAIN).pack(side="left", padx=8)

            days = b.get("days_until_expiry", 0)
            badge_text = f"Exp in {days}d" if days > 0 else "Expired"
            badge_var = "warning" if days > 0 else "danger"
            StatusBadge(row, text=badge_text, variant=badge_var, width=120).pack(side="left", padx=8)

    def _render_error(self, err_msg: str):
        self.card_meds.update_value("—", "API Offline")
        self.card_cats.update_value("—", "API Offline")
        self.card_batches.update_value("—", "API Offline")
        self.card_stock.update_value("—", "API Offline")
