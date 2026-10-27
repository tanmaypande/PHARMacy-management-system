import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.dialogs import AlertsModal


class TopHeader(ctk.CTkFrame):
    """
    Polished Healthcare SaaS Top Header Bar.
    Contains:
    - Sidebar collapse/expand toggle button
    - Dynamic page title and breadcrumbs
    - Quick search bar
    - Alert notifications bell with unread badge counter
    - Live database health pill
    - Theme toggle switch
    - Dr. Pharmacist profile card
    """
    def __init__(
        self,
        master,
        title: str = "Dashboard",
        subtitle: str = "Pharmacy Operational Management",
        api_client=None,
        on_toggle_theme=None,
        on_toggle_sidebar=None,
        on_search=None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.BG_CARD,
            height=66,
            corner_radius=0,
            border_width=0,
            **kwargs
        )
        self.api_client = api_client
        self.on_toggle_theme = on_toggle_theme
        self.on_toggle_sidebar = on_toggle_sidebar
        self.on_search = on_search
        self.current_alerts = []

        self.pack_propagate(False)
        self._build_header(title, subtitle)

    def _build_header(self, title: str, subtitle: str):
        # Left Box: Collapse Toggle & Page Titles
        left_box = ctk.CTkFrame(self, fg_color="transparent")
        left_box.pack(side="left", padx=(16, 20), pady=10)

        # 1. Sidebar Toggle Button
        if self.on_toggle_sidebar:
            self.btn_collapse = ctk.CTkButton(
                left_box,
                text="☰",
                width=36,
                height=36,
                corner_radius=8,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.TEXT_MAIN,
                font=accessibility_manager.get_font(14, weight="bold"),
                command=self.on_toggle_sidebar
            )
            self.btn_collapse.pack(side="left", padx=(0, 14))

        titles_box = ctk.CTkFrame(left_box, fg_color="transparent")
        titles_box.pack(side="left")

        self.lbl_title = ctk.CTkLabel(
            titles_box,
            text=title,
            font=accessibility_manager.get_font(17, weight="bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_sub = ctk.CTkLabel(
            titles_box,
            text=f"MediCare PMS  /  {subtitle}",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_sub.pack(anchor="w")

        # Right Box: Global Search, Alerts Bell, Health Pill, Theme Switch, Profile
        right_box = ctk.CTkFrame(self, fg_color="transparent")
        right_box.pack(side="right", padx=16, pady=12)

        # 2. Search Field
        self.search_entry = ctk.CTkEntry(
            right_box,
            placeholder_text="🔍 Search (Ctrl+F)...",
            width=210,
            height=34,
            corner_radius=8,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(12)
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<Return>", self._handle_search)

        # 3. Notification Bell with Badge
        self.btn_bell = ctk.CTkButton(
            right_box,
            text="🔔 0",
            width=54,
            height=34,
            corner_radius=8,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.TEXT_MAIN,
            font=accessibility_manager.get_font(11, weight="bold"),
            command=self._show_alerts
        )
        self.btn_bell.pack(side="left", padx=(0, 10))

        # 4. System Health Pill
        self.health_pill = ctk.CTkFrame(
            right_box,
            fg_color=Theme.BG_MUTED,
            corner_radius=8,
            height=34
        )
        self.health_pill.pack(side="left", padx=(0, 10))

        self.lbl_health = ctk.CTkLabel(
            self.health_pill,
            text="● API Online",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.SUCCESS_TEXT
        )
        self.lbl_health.pack(padx=10, pady=6)

        # 5. Theme Switcher Button (☀️ / 🌙)
        current_mode = accessibility_manager.config.get("appearance_mode", "light")
        theme_icon = "🌙 Dark" if current_mode == "light" else "☀️ Light"
        self.btn_theme = ctk.CTkButton(
            right_box,
            text=theme_icon,
            width=76,
            height=34,
            corner_radius=8,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(11, weight="bold"),
            command=self._handle_theme_toggle
        )
        self.btn_theme.pack(side="left", padx=(0, 12))

        # 6. User Profile Card
        user_card = ctk.CTkFrame(
            right_box,
            fg_color=Theme.BG_MUTED,
            corner_radius=8,
            height=36
        )
        user_card.pack(side="left")

        avatar_box = ctk.CTkLabel(
            user_card,
            text="🧑‍⚕️",
            font=accessibility_manager.get_font(15)
        )
        avatar_box.pack(side="left", padx=(8, 4), pady=4)

        user_info = ctk.CTkFrame(user_card, fg_color="transparent")
        user_info.pack(side="left", padx=(2, 10), pady=4)

        ctk.CTkLabel(
            user_info,
            text="Dr. Pharmacist",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            user_info,
            text="Admin Staff",
            font=accessibility_manager.get_font(10),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w")

    def set_title(self, title: str, subtitle: str):
        self.lbl_title.configure(text=title)
        self.lbl_sub.configure(text=f"MediCare PMS  /  {subtitle}")

    def update_health_status(self, is_online: bool, is_db_connected: bool):
        if is_online and is_db_connected:
            self.lbl_health.configure(text="● API & DB Online", text_color=Theme.SUCCESS_TEXT)
        elif is_online and not is_db_connected:
            self.lbl_health.configure(text="● DB Degraded", text_color=Theme.WARNING_TEXT)
        else:
            self.lbl_health.configure(text="● Backend Offline", text_color=Theme.DANGER_TEXT)

    def set_alerts(self, alerts: list):
        self.current_alerts = alerts or []
        count = len(self.current_alerts)
        if count > 0:
            self.btn_bell.configure(
                text=f"🔔 {count}",
                fg_color=Theme.WARNING_BG,
                text_color=Theme.WARNING_TEXT
            )
        else:
            self.btn_bell.configure(
                text="🔔 0",
                fg_color=Theme.SECONDARY,
                text_color=Theme.SECONDARY_TEXT
            )

    def _show_alerts(self):
        AlertsModal(self.winfo_toplevel(), alerts=self.current_alerts)

    def _handle_search(self, event=None):
        query = self.search_entry.get().strip()
        if self.on_search and query:
            self.on_search(query)

    def _handle_theme_toggle(self):
        accessibility_manager.toggle_mode()
        current_mode = accessibility_manager.config.get("appearance_mode", "light")
        self.btn_theme.configure(text="🌙 Dark" if current_mode == "light" else "☀️ Light")
        if self.on_toggle_theme:
            self.on_toggle_theme()
