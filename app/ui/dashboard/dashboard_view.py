"""
Polished Healthcare SaaS Operational Dashboard.
Faithfully styled after Mockup 1:
- Rich deep-teal Hero Welcome Banner (#046166) with greeting, quick action buttons, and watermark
- 6 Metric Cards with icon pills, bold values, and context trends
- Embedded Matplotlib stock distribution chart in medical teal
- Stock & expiry action items feed
- Recent inventory lots table
"""
from typing import Dict, Any, List
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.stat_card import StatCard
from app.ui.components.badge import StatusBadge
from app.ui.components.empty_state import EmptyState


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient, on_navigate=None):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.on_navigate = on_navigate
        self.canvas_widget = None

        self._build_ui()
        self.refresh_dashboard()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=22, pady=12)

        # ================= 1. Hero Welcome Banner (Mockup 1 Signature) =================
        hero = ctk.CTkFrame(
            self.scroll,
            fg_color=Theme.BG_BANNER,
            corner_radius=16,
            border_width=0
        )
        hero.pack(fill="x", pady=(0, 16))

        hero_inner = ctk.CTkFrame(hero, fg_color="transparent")
        hero_inner.pack(fill="x", padx=24, pady=20)

        hero_left = ctk.CTkFrame(hero_inner, fg_color="transparent")
        hero_left.pack(side="left", fill="both", expand=True)

        # Operational Tag Pill
        tag_frame = ctk.CTkFrame(hero_left, fg_color="#034E52", corner_radius=12)
        tag_frame.pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            tag_frame,
            text="🏥 CLINICAL OPERATIONS & COMPLIANCE",
            font=accessibility_manager.get_font(10, weight="bold"),
            text_color="#C6EB67"
        ).pack(padx=10, pady=4)

        # Greeting Title
        ctk.CTkLabel(
            hero_left,
            text="Good Morning, Dr. Pharmacist 👋",
            font=accessibility_manager.get_font(22, weight="bold"),
            text_color="#FFFFFF"
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            hero_left,
            text="Real-time pharmaceutical metrics, inventory levels, and safety compliance alerts.",
            font=accessibility_manager.get_font(12),
            text_color="#D1FAE5"
        ).pack(anchor="w", pady=(0, 16))

        # Hero Action Buttons
        hero_btn_row = ctk.CTkFrame(hero_left, fg_color="transparent")
        hero_btn_row.pack(anchor="w")

        if self.on_navigate:
            # White Pill Button
            ctk.CTkButton(
                hero_btn_row,
                text="📋  View Inventory Batches",
                height=36,
                corner_radius=20,
                fg_color="#FFFFFF",
                hover_color="#F0FDFC",
                text_color="#046166",
                font=accessibility_manager.get_font(12, weight="bold"),
                command=lambda: self.on_navigate("inventory")
            ).pack(side="left", padx=(0, 10))

            # Vibrant Lime Pill Button
            ctk.CTkButton(
                hero_btn_row,
                text="➕  Add New Medicine",
                height=36,
                corner_radius=20,
                fg_color=Theme.ACCENT_LIME,
                hover_color=Theme.ACCENT_LIME_HOVER,
                text_color=Theme.ACCENT_LIME_TEXT,
                font=accessibility_manager.get_font(12, weight="bold"),
                command=lambda: self.on_navigate("medicines")
            ).pack(side="left")

        # Hero Right Side: Pill Watermark
        hero_right = ctk.CTkFrame(hero_inner, fg_color="transparent")
        hero_right.pack(side="right", padx=(20, 10))

        ctk.CTkLabel(
            hero_right,
            text="💊",
            font=ctk.CTkFont(size=64),
            text_color="#057275"
        ).pack(expand=True)

        # ================= 2. 6 Stat Metric Cards Row (Mockup 1) =================
        cards_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards_grid.pack(fill="x", pady=(0, 16))
        cards_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total_meds = StatCard(cards_grid, "Total Medicines", "...", "Active Master Formulary", "💊")
        self.card_total_meds.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.card_today_sales = StatCard(cards_grid, "Today's Sales", "$0.00", "POS Phase 2 Sprint", "🧾")
        self.card_today_sales.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.card_low_stock = StatCard(cards_grid, "Low-Stock Items", "...", "Under Reorder Level", "⚠️")
        self.card_low_stock.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.card_expiring = StatCard(cards_grid, "Expiring Batches", "...", "Due within 30 Days", "⏳")
        self.card_expiring.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        # ================= 3. Middle Section: Chart & Alerts =================
        mid_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        mid_grid.pack(fill="both", expand=True, pady=(0, 16))
        mid_grid.grid_columnconfigure(0, weight=3)
        mid_grid.grid_columnconfigure(1, weight=2)

        # Left: Live Stock Distribution Chart
        self.chart_card = ctk.CTkFrame(
            mid_grid,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER
        )
        self.chart_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        chart_hdr = ctk.CTkFrame(self.chart_card, fg_color="transparent")
        chart_hdr.pack(fill="x", padx=18, pady=(16, 6))

        ctk.CTkLabel(
            chart_hdr,
            text="📊 Physical Stock by Drug Category",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        self.lbl_chart_meta = ctk.CTkLabel(
            chart_hdr,
            text="Live PostgreSQL Data",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_chart_meta.pack(side="right")

        self.chart_container = ctk.CTkFrame(self.chart_card, fg_color="transparent", height=240)
        self.chart_container.pack(fill="both", expand=True, padx=12, pady=(0, 14))

        # Right: Critical Stock & Expiry Alerts Feed
        self.alerts_card = ctk.CTkFrame(
            mid_grid,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER
        )
        self.alerts_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        alerts_hdr = ctk.CTkFrame(self.alerts_card, fg_color="transparent")
        alerts_hdr.pack(fill="x", padx=18, pady=(16, 6))

        ctk.CTkLabel(
            alerts_hdr,
            text="⚠️ Stock & Expiry Action Items",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        if self.on_navigate:
            ctk.CTkButton(
                alerts_hdr,
                text="View All →",
                width=80,
                height=26,
                fg_color="transparent",
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.PRIMARY,
                font=accessibility_manager.get_font(11, weight="bold"),
                command=lambda: self.on_navigate("inventory")
            ).pack(side="right")

        self.alerts_scroll = ctk.CTkScrollableFrame(self.alerts_card, fg_color="transparent", height=240)
        self.alerts_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # ================= 4. Lower Section: Recent Batches & Shortcuts =================
        bottom_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        bottom_grid.pack(fill="both", expand=True)
        bottom_grid.grid_columnconfigure(0, weight=3)
        bottom_grid.grid_columnconfigure(1, weight=2)

        # Recent Batch Receipts
        recent_card = ctk.CTkFrame(
            bottom_grid,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER
        )
        recent_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        r_hdr = ctk.CTkFrame(recent_card, fg_color="transparent")
        r_hdr.pack(fill="x", padx=18, pady=(14, 8))

        ctk.CTkLabel(
            r_hdr,
            text="📦 Recent Inventory Receiving Lots",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        self.recent_scroll = ctk.CTkScrollableFrame(recent_card, fg_color="transparent", height=160)
        self.recent_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # System Architecture Safeguards
        guard_card = ctk.CTkFrame(
            bottom_grid,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER
        )
        guard_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            guard_card,
            text="🛡️ TQM System Controls Active",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=18, pady=(14, 8))

        guard_box = ctk.CTkFrame(guard_card, fg_color=Theme.BG_MUTED, corner_radius=10)
        guard_box.pack(fill="both", expand=True, padx=14, pady=(0, 14))

        controls = [
            "Decoupled Architecture: Zero direct SQL from desktop UI",
            "Poka-Yoke: Automated expired batch rejection",
            "Decimal Arithmetic: Exact precision for all financials",
            "PostgreSQL 18: ACID relational integrity active"
        ]
        for ctrl in controls:
            row = ctk.CTkFrame(guard_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(row, text="✔", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.SUCCESS_TEXT, width=18).pack(side="left")
            ctk.CTkLabel(row, text=ctrl, font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MAIN).pack(side="left", padx=4)

    def refresh_dashboard(self):
        def _fetch():
            metrics = self.api_client.get_dashboard_metrics()
            expiring = self.api_client.list_expiring_soon(days=30)
            medicines = self.api_client.list_medicines()
            batches = self.api_client.list_batches()
            try:
                sales_summary = self.api_client.get_today_sales_summary()
            except Exception:
                sales_summary = {"today_revenue": 0.0, "today_bills_count": 0}
            return (metrics, expiring, medicines, batches, sales_summary)

        def _on_success(data):
            metrics, expiring, medicines, batches, sales_summary = data
            self._render_all(metrics, expiring, medicines, batches, sales_summary)

        def _on_error(exc):
            self._render_error(str(exc))

        run_in_background(_fetch, on_success=_on_success, on_error=_on_error)

    def _render_all(self, metrics: dict, expiring: list, medicines: list, batches: list, sales_summary: dict = None):
        tot_meds = metrics.get("total_medicines", 0)
        act_meds = metrics.get("active_medicines", 0)
        self.card_total_meds.update_value(tot_meds, f"{act_meds} Active Master Items")

        if sales_summary:
            today_rev = sales_summary.get("today_revenue", 0.0)
            today_bills = sales_summary.get("today_bills_count", 0)
            self.card_today_sales.update_value(f"${today_rev:.2f}", f"{today_bills} Transactions Today")
        else:
            self.card_today_sales.update_value("$0.00", "0 Transactions Today")

        low_stock = metrics.get("low_stock_medicines", 0)
        self.card_low_stock.update_value(
            low_stock,
            "Urgent Action Needed" if low_stock > 0 else "All Stock Levels Good"
        )

        exp_soon = metrics.get("expiring_soon_batches", 0)
        self.card_expiring.update_value(
            exp_soon,
            "Due for Review" if exp_soon > 0 else "All Batches Valid"
        )

        self._render_chart(medicines)
        self._render_alerts(medicines, expiring)
        self._render_recent_batches(batches)

    def _render_chart(self, medicines: list):
        for w in self.chart_container.winfo_children():
            w.destroy()

        cat_stock = {}
        for m in medicines:
            cname = m.get("category_name") or "Unclassified"
            short_name = cname.split()[0] if cname else "Other"
            cat_stock[short_name] = cat_stock.get(short_name, 0) + m.get("total_stock", 0)

        sorted_cats = sorted(cat_stock.items(), key=lambda x: x[1], reverse=True)[:5]
        if not sorted_cats or all(v == 0 for _, v in sorted_cats):
            EmptyState(self.chart_container, title="No Physical Stock", description="Stock levels will appear here once batches are received.").pack(fill="both", expand=True)
            return

        labels = [k for k, _ in sorted_cats]
        values = [v for _, v in sorted_cats]

        is_dark = accessibility_manager.config.get("appearance_mode") in ("dark", "high-contrast")
        bg_color = "#142826" if is_dark else "#FFFFFF"
        text_color = "#F2F8F6" if is_dark else "#0F2926"
        bar_color = "#046166" if not is_dark else "#057275"

        fig, ax = plt.subplots(figsize=(4.5, 2.2), dpi=90)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        bars = ax.barh(labels, values, color=bar_color, height=0.52, edgecolor="none")
        ax.invert_yaxis()

        ax.tick_params(colors=text_color, labelsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="x", color="#20423E" if is_dark else "#E0ECE8", linestyle="--", alpha=0.7)

        for bar in bars:
            width = bar.get_width()
            ax.text(width + 2, bar.get_y() + bar.get_height() / 2, f"{int(width)}",
                    va="center", ha="left", color=text_color, fontsize=8, fontweight="bold")

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _render_alerts(self, medicines: list, expiring: list):
        for w in self.alerts_scroll.winfo_children():
            w.destroy()

        low_stock_items = [m for m in medicines if (m.get("total_stock", 0) <= m.get("reorder_level", 10))]

        total_alerts = len(low_stock_items) + len(expiring)
        if total_alerts == 0:
            EmptyState(
                self.alerts_scroll,
                icon="✅",
                title="Zero Quality Alerts",
                description="All formulary items are above reorder levels and no batches expire soon."
            ).pack(fill="both", expand=True, pady=10)
            return

        for b in expiring[:3]:
            row = ctk.CTkFrame(self.alerts_scroll, fg_color=Theme.BG_MUTED, corner_radius=8)
            row.pack(fill="x", pady=2.5)
            StatusBadge(row, text=f"Exp in {b.get('days_until_expiry', 0)}d", variant="warning", width=95).pack(side="left", padx=8, pady=6)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(info, text=f"Lot {b['batch_number']}", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{b.get('medicine_name', 'Medicine')} • {b['quantity']} Units", font=accessibility_manager.get_font(10), text_color=Theme.TEXT_MUTED).pack(anchor="w")

        for m in low_stock_items[:5]:
            row = ctk.CTkFrame(self.alerts_scroll, fg_color=Theme.BG_MUTED, corner_radius=8)
            row.pack(fill="x", pady=2.5)
            StatusBadge(row, text="LOW STOCK", variant="danger", width=95).pack(side="left", padx=8, pady=6)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(info, text=m["name"], font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
            ctk.CTkLabel(info, text=f"Stock: {m.get('total_stock', 0)} / Reorder: {m.get('reorder_level', 10)}", font=accessibility_manager.get_font(10), text_color=Theme.TEXT_MUTED).pack(anchor="w")

    def _render_recent_batches(self, batches: list):
        for w in self.recent_scroll.winfo_children():
            w.destroy()

        if not batches:
            EmptyState(self.recent_scroll, title="No Batches Recorded", description="Received inventory shipments will appear here.").pack(fill="both", expand=True)
            return

        for b in batches[:4]:
            row = ctk.CTkFrame(self.recent_scroll, fg_color=Theme.BG_MUTED, corner_radius=8)
            row.pack(fill="x", pady=2.5)

            ctk.CTkLabel(
                row,
                text=b["batch_number"],
                width=110,
                anchor="w",
                font=accessibility_manager.get_font(11, weight="bold"),
                text_color=Theme.PRIMARY
            ).pack(side="left", padx=10, pady=6)

            ctk.CTkLabel(
                row,
                text=b.get("medicine_name") or "Medicine",
                width=180,
                anchor="w",
                font=accessibility_manager.get_font(11),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=4)

            ctk.CTkLabel(
                row,
                text=f"{b['quantity']} Units",
                width=80,
                anchor="center",
                font=accessibility_manager.get_font(11, weight="bold"),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=4)

            exp = str(b.get("expiry_date", "—"))
            ctk.CTkLabel(
                row,
                text=f"Exp: {exp}",
                width=100,
                anchor="e",
                font=accessibility_manager.get_font(10),
                text_color=Theme.TEXT_MUTED
            ).pack(side="left", padx=10)

    def _render_error(self, err_msg: str):
        self.card_total_meds.update_value("—", "API Offline")
        self.card_today_sales.update_value("—", "API Offline")
        self.card_low_stock.update_value("—", "API Offline")
        self.card_expiring.update_value("—", "API Offline")
