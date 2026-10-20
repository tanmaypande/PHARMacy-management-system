import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager


class TopHeader(ctk.CTkFrame):
    """
    Polished Healthcare SaaS Top Header Bar.
    Contains page title, search/connection indicators, theme toggle, and pharmacist profile badge.
    """
    def __init__(
        self,
        master,
        title: str = "Dashboard",
        subtitle: str = "Pharmacy Operational Management",
        api_client=None,
        on_toggle_theme=None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.BG_CARD,
            height=68,
            corner_radius=0,
            border_width=0,
            **kwargs
        )
        self.api_client = api_client
        self.on_toggle_theme = on_toggle_theme

        # Prevent frame from shrinking
        self.pack_propagate(False)

        self._build_header(title, subtitle)

    def _build_header(self, title: str, subtitle: str):
        # Left Side: Page Title and Breadcrumb
        left_box = ctk.CTkFrame(self, fg_color="transparent")
        left_box.pack(side="left", padx=24, pady=10)

        self.lbl_title = ctk.CTkLabel(
            left_box,
            text=title,
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_sub = ctk.CTkLabel(
            left_box,
            text=f"MediCare PMS  /  {subtitle}",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_sub.pack(anchor="w")

        # Right Side: System Status, Theme Toggle, User Profile
        right_box = ctk.CTkFrame(self, fg_color="transparent")
        right_box.pack(side="right", padx=24, pady=12)

        # 1. System Health Pill
        self.health_pill = ctk.CTkFrame(
            right_box,
            fg_color=Theme.BG_MUTED,
            corner_radius=8,
            height=34
        )
        self.health_pill.pack(side="left", padx=(0, 12))

        self.lbl_health = ctk.CTkLabel(
            self.health_pill,
            text="● API Connected",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.SUCCESS_TEXT
        )
        self.lbl_health.pack(padx=10, pady=6)

        # 2. Theme Switcher Button (☀️ / 🌙)
        current_mode = accessibility_manager.config.get("appearance_mode", "light")
        theme_icon = "🌙 Dark" if current_mode == "light" else "☀️ Light"
        self.btn_theme = ctk.CTkButton(
            right_box,
            text=theme_icon,
            width=80,
            height=34,
            corner_radius=8,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(12, weight="bold"),
            command=self._handle_theme_toggle
        )
        self.btn_theme.pack(side="left", padx=(0, 14))

        # 3. User Profile Card
        user_card = ctk.CTkFrame(
            right_box,
            fg_color=Theme.BG_MUTED,
            corner_radius=8,
            height=36
        )
        user_card.pack(side="left")

        # Avatar circle
        avatar_box = ctk.CTkLabel(
            user_card,
            text="🧑‍⚕️",
            font=ctk.CTkFont(size=accessibility_manager.get_font_size(16))
        )
        avatar_box.pack(side="left", padx=(8, 4), pady=4)

        user_info = ctk.CTkFrame(user_card, fg_color="transparent")
        user_info.pack(side="left", padx=(2, 10), pady=4)

        ctk.CTkLabel(
            user_info,
            text="Dr. Pharmacist",
            font=accessibility_manager.get_font(12, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            user_info,
            text="Admin / Staff",
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

    def _handle_theme_toggle(self):
        accessibility_manager.toggle_mode()
        current_mode = accessibility_manager.config.get("appearance_mode", "light")
        self.btn_theme.configure(text="🌙 Dark" if current_mode == "light" else "☀️ Light")
        if self.on_toggle_theme:
            self.on_toggle_theme()
