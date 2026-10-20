"""
Polished Healthcare SaaS Operational Dashboard.
Provides:
- 4 Primary Summary Cards (Total Medicines, Today's Sales, Low-Stock Medicines, Expiring Medicines)
- Live Stock Distribution Chart via Matplotlib embedded in CustomTkinter
- Critical Stock & Expiry Alerts feed from PostgreSQL
- Recent Inventory Activity log & quick actions
"""
import threading
from typing import Dict, Any, List
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
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
        # Scrollable container so it fits comfortably on any screen height
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Action & Filter Bar
        action_bar = ctk.CTkFrame(self.scroll, fg_color="transparent")
        action_bar.pack(fill="x", pady=(0, 14))

        title_box = ctk.CTkFrame(action_bar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="Clinical Operations & Performance Dashboard",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Real-time pharmaceutical metrics, inventory levels, and safety compliance alerts",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

        ctk.CTkButton(
            action_bar,
            text="🔄 Refresh Data",
            width=110,
            height=34,
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(12, weight="bold"),
            command=self.refresh_dashboard
        ).pack(side="right")

        # 2. Four Primary Summary Cards (Requirement: Total medicines, Today's sales, Low-stock, Expiring)
        cards_grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards_grid.pack(fill="x", pady=(0, 16))
        cards_grid.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total_meds = StatCard(cards_grid, "Total Medicines", "...", "Active Master Formulary", "💊")
        self.card_total_meds.grid(row=0, column=0, padx=6, pady=4, sticky="nsew")

        self.card_today_sales = StatCard(cards_grid, "Today's Sales", "$0.00", "POS Inactive • Phase 2 Sprint", "🧾")
        self.card_today_sales.grid(row=0, column=1, padx=6, pady=4, sticky="nsew")

        self.card_low_stock = StatCard(cards_grid, "Low-Stock Medicines", "...", "Under Reorder Level", "⚠️")
        self.card_low_stock.grid(row=0, column=2, padx=6, pady=4, sticky="nsew")

        self.card_expiring = StatCard(cards_grid, "Expiring Medicines", "...", "Due within 30 Days", "⏳")
        self.card_expiring.grid(row=0, column=3, padx=6, pady=4, sticky="nsew")

        # 3. Middle Section: Analytics Chart & Stock Alerts Feed
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
        chart_hdr.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            chart_hdr,
            text="📊 Physical Stock by Drug Category",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        self.chart_container = ctk.CTkFrame(self.chart_card, fg_color="transparent", height=240)
        self.chart_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

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
        alerts_hdr.pack(fill="x", padx=16, pady=(14, 6))

        ctk.CTkLabel(
            alerts_hdr,
            text="⚠️ Stock & Expiry Action Items",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        if self.on_navigate:
            ctk.CTkButton(
                alerts_hdr,
                text="View Inventory →",
                width=110,
                height=26,
                fg_color="transparent",
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.PRIMARY,
                font=accessibility_manager.get_font(11, weight="bold"),
                command=lambda: self.on_navigate("inventory")
            ).pack(side="right")

        self.alerts_scroll = ctk.CTkScrollableFrame(self.alerts_card, fg_color="transparent", height=240)
        self.alerts_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # 4. Lower Section: Recent Batches Activity & Quick Shortcuts
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
        r_hdr.pack(fill="x", padx=16, pady=(14, 8))

        ctk.CTkLabel(
            r_hdr,
            text="📦 Recent Inventory Receiving Lots",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        self.recent_scroll = ctk.CTkScrollableFrame(recent_card, fg_color="transparent", height=160)
        self.recent_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Quick Actions & Architectural Guard
        side_card = ctk.CTkFrame(
            bottom_grid,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER
        )
        side_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            side_card,
            text="⚡ Clinical Shortcuts",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=16, pady=(14, 10))

        if self.on_navigate:
            ctk.CTkButton(
                side_card,
                text="➕  Register New Medicine",
                height=36,
                corner_radius=Theme.RADIUS_BUTTON,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                font=accessibility_manager.get_font(12, weight="bold"),
                command=lambda: self.on_navigate("medicines")
            ).pack(fill="x", padx=16, pady=3)

            ctk.CTkButton(
                side_card,
                text="📦  Receive Inventory Batch",
                height=36,
                corner_radius=Theme.RADIUS_BUTTON,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                font=accessibility_manager.get_font(12, weight="bold"),
                command=lambda: self.on_navigate("inventory")
            ).pack(fill="x", padx=16, pady=3)

            ctk.CTkButton(
                side_card,
                text="🗂  Manage Drug Categories",
                height=36,
                corner_radius=Theme.RADIUS_BUTTON,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                font=accessibility_manager.get_font(12, weight="bold"),
                command=lambda: self.on_navigate("categories")
            ).pack(fill="x", padx=16, pady=3)

        info_box = ctk.CTkFrame(side_card, fg_color=Theme.BG_MUTED, corner_radius=8)
        info_box.pack(fill="x", padx=16, pady=(12, 14))

        ctk.CTkLabel(
            info_box,
            text="🛡️ TQM System Controls Active",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            info_box,
            text="• Direct DB connections blocked from UI client\n"
                 "• Poka-Yoke expired batch prevention active\n"
                 "• Decimal arithmetic prevents rounding error",
            font=accessibility_manager.get_font(10),
            text_color=Theme.TEXT_MUTED,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 8))

    def refresh_dashboard(self):
        def _fetch():
            try:
                metrics = self.api_client.get_dashboard_metrics()
                expiring = self.api_client.list_expiring_soon(days=30)
                medicines = self.api_client.list_medicines()
                batches = self.api_client.list_batches()
                self.after(0, self._render_all, metrics, expiring, medicines, batches)
            except Exception as exc:
                self.after(0, self._render_error, str(exc))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_all(self, metrics: dict, expiring: list, medicines: list, batches: list):
        # 1. Render Summary Cards
        tot_meds = metrics.get("total_medicines", 0)
        act_meds = metrics.get("active_medicines", 0)
        self.card_total_meds.update_value(tot_meds, f"{act_meds} Active Master Items")

        self.card_today_sales.update_value("$0.00", "POS In Development • Phase 2")

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

        # 2. Render Chart: Stock by Category
        self._render_chart(medicines)

        # 3. Render Stock & Expiry Alerts
        self._render_alerts(medicines, expiring)

        # 4. Render Recent Batches
        self._render_recent_batches(batches)

    def _render_chart(self, medicines: list):
        for w in self.chart_container.winfo_children():
            w.destroy()

        # Aggregate stock by category
        cat_stock = {}
        for m in medicines:
            cname = m.get("category_name") or "Unclassified"
            # Simplify long category names
            short_name = cname.split()[0] if cname else "Other"
            cat_stock[short_name] = cat_stock.get(short_name, 0) + m.get("total_stock", 0)

        # Filter top 6 categories
        sorted_cats = sorted(cat_stock.items(), key=lambda x: x[1], reverse=True)[:6]
        if not sorted_cats or all(v == 0 for _, v in sorted_cats):
            EmptyState(self.chart_container, title="No Physical Stock", description="Stock levels will appear here once batches are received.").pack(fill="both", expand=True)
            return

        labels = [k for k, _ in sorted_cats]
        values = [v for _, v in sorted_cats]

        # Determine theme colors
        is_dark = accessibility_manager.config.get("appearance_mode") in ("dark", "high-contrast")
        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        text_color = "#F8FAFC" if is_dark else "#0F172A"
        bar_color = "#3B82F6" if is_dark else "#2563EB"

        fig, ax = plt.subplots(figsize=(4.5, 2.2), dpi=90)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)

        bars = ax.barh(labels, values, color=bar_color, height=0.55, edgecolor="none")
        ax.invert_yaxis()  # Top down

        # Clean axis styling
        ax.tick_params(colors=text_color, labelsize=9)
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.grid(axis="x", color="#334155" if is_dark else "#E2E8F0", linestyle="--", alpha=0.6)

        # Add data labels on bars
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

        # Find low stock medicines
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

        # Show expiring batches first
        for b in expiring[:3]:
            row = ctk.CTkFrame(self.alerts_scroll, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", pady=2)
            StatusBadge(row, text=f"Exp in {b.get('days_until_expiry', 0)}d", variant="warning", width=95).pack(side="left", padx=8, pady=6)
            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True, padx=4)
            ctk.CTkLabel(info, text=f"Lot {b['batch_number']}", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
            ctk.CTkLabel(info, text=f"{b.get('medicine_name', 'Medicine')} • {b['quantity']} Units", font=accessibility_manager.get_font(10), text_color=Theme.TEXT_MUTED).pack(anchor="w")

        # Show low stock medicines
        for m in low_stock_items[:5]:
            row = ctk.CTkFrame(self.alerts_scroll, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", pady=2)
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
            row = ctk.CTkFrame(self.recent_scroll, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", pady=2)

            ctk.CTkLabel(
                row,
                text=b["batch_number"],
                width=110,
                anchor="w",
                font=accessibility_manager.get_font(11, weight="bold"),
                text_color=Theme.PRIMARY
            ).pack(side="left", padx=8, pady=6)

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
            ).pack(side="left", padx=8)

    def _render_error(self, err_msg: str):
        self.card_total_meds.update_value("—", "API Offline")
        self.card_today_sales.update_value("—", "API Offline")
        self.card_low_stock.update_value("—", "API Offline")
        self.card_expiring.update_value("—", "API Offline")
