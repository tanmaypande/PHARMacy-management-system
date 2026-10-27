import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager


class StatusBadge(ctk.CTkFrame):
    """
    Standardized healthcare status badge.
    Combines text + icon so status never relies on color alone (Q12 Accessibility requirement).
    """
    def __init__(self, master, text: str, variant: str = "neutral", **kwargs):
        super().__init__(master, corner_radius=6, **kwargs)

        variant = variant.lower()
        if variant in ("success", "active", "valid"):
            bg_col = Theme.SUCCESS_BG
            text_col = Theme.SUCCESS_TEXT
            prefix = "● "
        elif variant in ("warning", "expiring", "low_stock"):
            bg_col = Theme.WARNING_BG
            text_col = Theme.WARNING_TEXT
            prefix = "▲ "
        elif variant in ("danger", "expired", "archived", "error"):
            bg_col = Theme.DANGER_BG
            text_col = Theme.DANGER_TEXT
            prefix = "■ "
        elif variant in ("info", "sku"):
            bg_col = Theme.INFO_BG
            text_col = Theme.INFO_TEXT
            prefix = ""
        else:
            bg_col = Theme.BG_MUTED
            text_col = Theme.TEXT_MUTED
            prefix = "○ "

        self.prefix = prefix
        self.configure(fg_color=bg_col)
        self.label = ctk.CTkLabel(
            self,
            text=f"{self.prefix}{text}",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=text_col
        )
        self.label.pack(padx=8, pady=3)

    def update_text(self, text: str):
        self.label.configure(text=f"{self.prefix}{text}")
