import customtkinter as ctk
from app.ui.accessibility.accessibility_manager import accessibility_manager


class SettingsView(ctk.CTkFrame):
    def __init__(self, master, on_theme_change=None):
        super().__init__(master, fg_color="transparent")
        self.on_theme_change = on_theme_change
        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="⚙ Accessibility & Interface Settings (TQM Q12)",
            font=accessibility_manager.get_font(20, weight="bold")
        ).pack(side="left")

        container = ctk.CTkFrame(self, fg_color=accessibility_manager.get_card_fg(), corner_radius=12)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        # Appearance / Theme Mode
        ctk.CTkLabel(
            container,
            text="Visual Theme & Contrast Mode",
            font=accessibility_manager.get_font(16, weight="bold")
        ).pack(anchor="w", padx=25, pady=(20, 5))

        ctk.CTkLabel(
            container,
            text="Choose between Standard Dark, Clean Light, or High-Contrast Mode for optimal readability.",
            font=accessibility_manager.get_font(13),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=25, pady=(0, 10))

        self.theme_var = ctk.StringVar(value=accessibility_manager.config.get("appearance_mode", "dark"))
        modes_row = ctk.CTkFrame(container, fg_color="transparent")
        modes_row.pack(anchor="w", padx=25, pady=(0, 20))

        for mode in [("Dark Mode", "dark"), ("Light Mode", "light"), ("High Contrast (Q12)", "high-contrast")]:
            ctk.CTkRadioButton(
                modes_row,
                text=mode[0],
                value=mode[1],
                variable=self.theme_var,
                command=self._apply_theme,
                font=accessibility_manager.get_font(13)
            ).pack(side="left", padx=(0, 20))

        # Font Scaling Section
        ctk.CTkLabel(
            container,
            text="Dynamic Font Size & Scaling",
            font=accessibility_manager.get_font(16, weight="bold")
        ).pack(anchor="w", padx=25, pady=(10, 5))

        self.scale_label = ctk.CTkLabel(
            container,
            text=f"Current Scale: {int(accessibility_manager.config.get('font_scale', 1.0) * 100)}%",
            font=accessibility_manager.get_font(13),
            text_color="#38BDF8"
        )
        self.scale_label.pack(anchor="w", padx=25, pady=(0, 10))

        slider_row = ctk.CTkFrame(container, fg_color="transparent")
        slider_row.pack(fill="x", padx=25, pady=(0, 20))

        self.slider = ctk.CTkSlider(
            slider_row,
            from_=1.0,
            to=1.4,
            number_of_steps=4,
            command=self._on_slider_change,
            width=320
        )
        self.slider.set(accessibility_manager.config.get("font_scale", 1.0))
        self.slider.pack(side="left")

        # System Architecture Info Card
        info_frame = ctk.CTkFrame(container, fg_color="#1E293B", corner_radius=10)
        info_frame.pack(fill="x", padx=25, pady=20)

        ctk.CTkLabel(
            info_frame,
            text="System Architecture & Integrity Controls",
            font=accessibility_manager.get_font(14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            info_frame,
            text="• CustomTkinter Desktop Client -> FastAPI Backend -> PostgreSQL 18\n"
                 "• UI strictly communicates over HTTP API (zero direct SQL access from client)\n"
                 "• Total Quality Management (TQM): Expired batches blocked at database & service levels\n"
                 "• Decimal arithmetic prevents float rounding errors in financial transactions",
            font=accessibility_manager.get_font(12),
            text_color="#94A3B8",
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 12))

    def _apply_theme(self):
        new_mode = self.theme_var.get()
        accessibility_manager.set_appearance_mode(new_mode)
        if self.on_theme_change:
            self.on_theme_change()

    def _on_slider_change(self, val):
        self.scale_label.configure(text=f"Current Scale: {int(val * 100)}%")
        accessibility_manager.set_font_scale(val)
        if self.on_theme_change:
            self.on_theme_change()
