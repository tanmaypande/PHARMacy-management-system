import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager


class StatCard(ctk.CTkFrame):
    """
    Polished Healthcare SaaS KPI card.
    Displays an icon, primary value, label, and status indicator with subtle borders.
    """
    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtitle: str,
        icon: str,
        accent_color=None,
        **kwargs
    ):
        super().__init__(
            master,
            fg_color=Theme.BG_CARD,
            corner_radius=12,
            border_width=1,
            border_color=Theme.BORDER,
            **kwargs
        )
        self.accent_color = accent_color or Theme.PRIMARY

        # Top row: icon and indicator
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=18, pady=(16, 4))

        # Icon pill
        icon_box = ctk.CTkFrame(
            top_row,
            fg_color=Theme.BG_MUTED,
            width=38,
            height=38,
            corner_radius=8
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)

        ctk.CTkLabel(
            icon_box,
            text=icon,
            font=accessibility_manager.get_font(18)
        ).pack(expand=True)

        # Title / Category in uppercase subtle text
        ctk.CTkLabel(
            self,
            text=title.upper(),
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", padx=18, pady=(8, 2))

        # Primary Big Value
        self.val_label = ctk.CTkLabel(
            self,
            text=value,
            font=accessibility_manager.get_font(28, weight="bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.val_label.pack(anchor="w", padx=18, pady=(0, 4))

        # Subtitle context note
        self.sub_label = ctk.CTkLabel(
            self,
            text=subtitle,
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.sub_label.pack(anchor="w", padx=18, pady=(0, 16))

    def update_value(self, value: str, subtitle: str = None):
        self.val_label.configure(text=str(value))
        if subtitle:
            self.sub_label.configure(text=subtitle)
