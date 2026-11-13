import customtkinter as ctk
from typing import Dict, Any, Optional
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.ui.billing.billing_view import BillingView
from app.client.api_client import APIClient


class CashierView(ctk.CTkFrame):
    """
    Panel 4: Cashier / Sales Executive Panel
    Dedicated POS counter station for fast checkout, scanning, multiple payment methods
    (Cash, UPI, Card), thermal receipts, returns, and daily sales register.
    """
    def __init__(self, parent, api_client: APIClient):
        super().__init__(parent, fg_color=Theme.BG_APP)
        self.api_client = api_client

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Cashier POS Top Bar
        top_bar = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, height=48, corner_radius=10, border_width=1, border_color=Theme.BORDER)
        top_bar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            top_bar,
            text="🧾 Cashier Point of Sale (POS) Counter — Live Register",
            font=accessibility_manager.get_font(15, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left", padx=16)

        ctk.CTkLabel(
            top_bar,
            text="Supported: 💵 Cash  •  📱 UPI Instant  •  💳 Debit/Credit Card",
            font=accessibility_manager.get_font(12, weight="bold"),
            text_color=Theme.PRIMARY
        ).pack(side="right", padx=16)

        # 2. Embedded High-Speed POS Counter
        self.billing_view = BillingView(self, self.api_client)
        self.billing_view.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 16))
