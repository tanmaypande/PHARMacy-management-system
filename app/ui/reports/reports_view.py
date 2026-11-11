"""
TQM Quality Analytics & Financial Reports View.
Features live Matplotlib performance trend charts, inventory valuation cards, and CSV exports.
"""
from typing import Optional, Dict, Any, List
import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.stat_card import StatCard


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.chart_canvas = None

        self._build_ui()
        self.load_data()

    def _build_ui(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="📈 TQM Quality Analytics & Executive Reports",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            title_box,
            text="Financial performance, inventory valuation, and Pareto quality indicators",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_subtitle.pack(anchor="w")

        btn_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_row.pack(side="right")

        self.btn_export = ctk.CTkButton(
            btn_row,
            text="📥 Export CSV",
            width=120,
            height=36,
            fg_color=Theme.SECONDARY,
            text_color=Theme.SECONDARY_TEXT,
            command=self._export_csv
        )
        self.btn_export.pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=90,
            height=36,
            fg_color=Theme.PRIMARY,
            command=self.load_data
        ).pack(side="left", padx=5)

        # Stat Cards Grid (4 Cards)
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=(0, 15))
        cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="c")

        self.card_rev = StatCard(cards_frame, title="30-Day Revenue", value="₹0.00", icon="💰", variant="primary")
        self.card_rev.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.card_profit = StatCard(cards_frame, title="Estimated Gross Margin", value="₹0.00", icon="📈", variant="success")
        self.card_profit.grid(row=0, column=1, sticky="ew", padx=3)

        self.card_inventory = StatCard(cards_frame, title="Stock Cost Valuation", value="₹0.00", icon="📦", variant="info")
        self.card_inventory.grid(row=0, column=2, sticky="ew", padx=3)

        self.card_retail = StatCard(cards_frame, title="Stock Retail Potential", value="₹0.00", icon="🏷️", variant="warning")
        self.card_retail.grid(row=0, column=3, sticky="ew", padx=(6, 0))

        # Chart Container
        self.chart_container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        self.chart_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def load_data(self):
        def _fetch():
            sales_rep = self.api_client.get_sales_report(days=30)
            inv_val = self.api_client.get_inventory_valuation()
            return sales_rep, inv_val

        run_in_background(
            _fetch,
            on_success=self._on_loaded,
            on_error=lambda err: print("Error loading reports:", err)
        )

    def _on_loaded(self, result):
        sales_rep, inv_val = result

        # Update cards
        self.card_rev.update_value(f"₹{sales_rep.get('total_revenue', 0):,.2f}")
        self.card_profit.update_value(f"₹{sales_rep.get('total_profit', 0):,.2f}")
        self.card_inventory.update_value(f"₹{inv_val.get('total_cost_value', 0):,.2f}")
        self.card_retail.update_value(f"₹{inv_val.get('total_retail_value', 0):,.2f}")

        # Render Chart
        self._render_trend_chart(sales_rep.get("daily_trend", []))

    def _render_trend_chart(self, daily_trend):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        if not daily_trend:
            ctk.CTkLabel(
                self.chart_container,
                text="No recent sales activity to display in chart.",
                font=accessibility_manager.get_font(13),
                text_color=Theme.TEXT_MUTED
            ).pack(expand=True)
            return

        dates = [d["date"][-5:] for d in daily_trend]
        amounts = [d["amount"] for d in daily_trend]

        is_dark = accessibility_manager.config.get("appearance_mode", "light") == "dark"
        bg_color = "#1E293B" if is_dark else "#FFFFFF"
        text_color = "#E2E8F0" if is_dark else "#334155"

        fig = Figure(figsize=(7, 3.2), dpi=100, facecolor=bg_color)
        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)

        ax.plot(dates, amounts, color="#0D9488", linewidth=2.5, marker="o", markersize=6, label="Daily Revenue (₹)")
        ax.fill_between(dates, amounts, color="#0D9488", alpha=0.15)

        ax.set_title("30-Day Dispensation Revenue Trend", color=text_color, fontsize=12, fontweight="bold", pad=12)
        ax.tick_params(colors=text_color, labelsize=9)
        for spine in ax.spines.values():
            spine.set_color("#64748B" if is_dark else "#CBD5E1")
        ax.grid(True, linestyle="--", alpha=0.3, color="#64748B")

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=12)

    def _export_csv(self):
        self.btn_export.configure(state="disabled", text="Exporting...")

        def _do():
            return self.api_client.export_sales_csv(days=30)

        def _done(res):
            self.btn_export.configure(state="normal", text="📥 Export CSV")
            import tkinter.messagebox as msg
            msg.showinfo("Export Successful", f"Sales report successfully exported to:\n{res.get('file_path')}")

        run_in_background(_do, on_success=_done, on_error=lambda err: self.btn_export.configure(state="normal", text="📥 Export CSV"))
