import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager


class EmptyState(ctk.CTkFrame):
    """
    Polished empty state widget for data tables and lists.
    """
    def __init__(
        self,
        master,
        icon: str = "🔍",
        title: str = "No Records Found",
        description: str = "There are currently no items matching your criteria.",
        action_text: str = None,
        action_command=None,
        **kwargs
    ):
        super().__init__(master, fg_color="transparent", **kwargs)

        # Icon
        ctk.CTkLabel(
            self,
            text=icon,
            font=ctk.CTkFont(size=accessibility_manager.get_font_size(44))
        ).pack(pady=(30, 8))

        # Title
        ctk.CTkLabel(
            self,
            text=title,
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(pady=(0, 4))

        # Description
        ctk.CTkLabel(
            self,
            text=description,
            font=accessibility_manager.get_font(13),
            text_color=Theme.TEXT_MUTED,
            justify="center"
        ).pack(pady=(0, 16))

        # Action Button (optional)
        if action_text and action_command:
            ctk.CTkButton(
                self,
                text=action_text,
                height=36,
                fg_color=Theme.PRIMARY,
                hover_color=Theme.PRIMARY_HOVER,
                font=accessibility_manager.get_font(13, weight="bold"),
                command=action_command
            ).pack(pady=(0, 20))
