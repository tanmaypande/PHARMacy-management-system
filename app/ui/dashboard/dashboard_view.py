import threading
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.accessibility.accessibility_manager import accessibility_manager


class DashboardView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient, on_navigate=None):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self.on_navigate = on_navigate
        self._build_ui()
        self.refresh_metrics()

    def _build_ui(self):
        # Header banner
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            header,
            text="Operational Overview & Quality Monitoring",
            font=accessibility_manager.get_font(20, weight="bold")
        )
        title.pack(side="left")

        btn_refresh = ctk.CTkButton(
            header,
            text="🔄 Refresh",
            width=100,
            command=self.refresh_metrics,
            font=accessibility_manager.get_font(13)
        )
        btn_refresh.pack(side="right")

        # Metric Cards Grid Container
        self.cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.cards_frame.pack(fill="x", padx=15, pady=10)

        # 4 Columns of Cards
        self.card_meds = self._create_card(self.cards_frame, "Active Medicines", "...", "💊", "#3B82F6")
        self.card_meds.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.card_cats = self._create_card(self.cards_frame, "Drug Categories", "...", "🗂", "#8B5CF6")
        self.card_cats.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        self.card_batches = self._create_card(self.cards_frame, "Active Batches", "...", "📦", "#10B981")
        self.card_batches.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

        self.card_stock = self._create_card(self.cards_frame, "Total Stock Units", "...", "🔢", "#06B6D4")
        self.card_stock.grid(row=0, column=3, padx=8, pady=8, sticky="nsew")

        # Quality Alert Cards Row (TQM Focus)
        self.alerts_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.alerts_frame.pack(fill="x", padx=15, pady=10)

        self.card_low_stock = self._create_card(self.alerts_frame, "Low Stock Alerts", "...", "⚠️", "#F59E0B")
        self.card_low_stock.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.card_expiring = self._create_card(self.alerts_frame, "Expiring Soon (<30 Days)", "...", "⏳", "#EF4444")
        self.card_expiring.grid(row=0, column=1, padx=8, pady=8, sticky="nsew")

        self.card_expired = self._create_card(self.alerts_frame, "Expired Batches Blocked", "...", "🛑", "#991B1B")
        self.card_expired.grid(row=0, column=2, padx=8, pady=8, sticky="nsew")

        self.cards_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.alerts_frame.grid_columnconfigure((0, 1, 2), weight=1)

        # Action Shortcuts Frame
        actions_frame = ctk.CTkFrame(self, fg_color=accessibility_manager.get_card_fg(), corner_radius=10)
        actions_frame.pack(fill="x", padx=20, pady=20)

        act_title = ctk.CTkLabel(
            actions_frame,
            text="Quick Workflow Shortcuts",
            font=accessibility_manager.get_font(15, weight="bold")
        )
        act_title.pack(anchor="w", padx=20, pady=(15, 10))

        btn_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        if self.on_navigate:
            ctk.CTkButton(
                btn_row,
                text="💊 Manage Medicines",
                command=lambda: self.on_navigate("medicines"),
                font=accessibility_manager.get_font(13)
            ).pack(side="left", padx=(0, 10))

            ctk.CTkButton(
                btn_row,
                text="🗂 Manage Categories",
                command=lambda: self.on_navigate("categories"),
                font=accessibility_manager.get_font(13)
            ).pack(side="left", padx=10)

            ctk.CTkButton(
                btn_row,
                text="📦 Manage Inventory Batches",
                command=lambda: self.on_navigate("inventory"),
                font=accessibility_manager.get_font(13)
            ).pack(side="left", padx=10)

    def _create_card(self, parent, title: str, initial_val: str, icon: str, border_color: str):
        card = ctk.CTkFrame(
            parent,
            fg_color=accessibility_manager.get_card_fg(),
            corner_radius=10,
            border_width=2,
            border_color=border_color
        )

        icon_lbl = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=accessibility_manager.get_font_size(24)))
        icon_lbl.pack(anchor="w", padx=15, pady=(12, 0))

        val_lbl = ctk.CTkLabel(
            card,
            text=initial_val,
            font=accessibility_manager.get_font(26, weight="bold")
        )
        val_lbl.pack(anchor="w", padx=15, pady=(2, 2))

        title_lbl = ctk.CTkLabel(
            card,
            text=title,
            font=accessibility_manager.get_font(12),
            text_color="#94A3B8"
        )
        title_lbl.pack(anchor="w", padx=15, pady=(0, 12))

        card.val_lbl = val_lbl
        return card

    def refresh_metrics(self):
        def _fetch():
            try:
                metrics = self.api_client.get_dashboard_metrics()
                self.after(0, self._update_ui, metrics)
            except Exception as exc:
                self.after(0, self._show_error, str(exc))

        threading.Thread(target=_fetch, daemon=True).start()

    def _update_ui(self, m: dict):
        self.card_meds.val_lbl.configure(text=str(m.get("active_medicines", 0)))
        self.card_cats.val_lbl.configure(text=str(m.get("total_categories", 0)))
        self.card_batches.val_lbl.configure(text=str(m.get("total_batches", 0)))
        self.card_stock.val_lbl.configure(text=str(m.get("total_stock_units", 0)))
        self.card_low_stock.val_lbl.configure(text=str(m.get("low_stock_medicines", 0)))
        self.card_expiring.val_lbl.configure(text=str(m.get("expiring_soon_batches", 0)))
        self.card_expired.val_lbl.configure(text=str(m.get("expired_batches", 0)))

    def _show_error(self, err_msg: str):
        self.card_meds.val_lbl.configure(text="Err")
