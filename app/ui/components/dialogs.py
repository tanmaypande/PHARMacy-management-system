import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager


class ConfirmDialog(ctk.CTkToplevel):
    """
    Accessible confirmation modal for destructive or critical actions.
    """
    def __init__(
        self,
        master,
        title: str = "Confirm Action",
        message: str = "Are you sure you want to proceed with this operation?",
        confirm_text: str = "Confirm",
        is_destructive: bool = False,
        on_confirm=None
    ):
        super().__init__(master)
        self.on_confirm = on_confirm

        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.grab_set()

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        # Warning icon & title
        icon = "⚠️" if is_destructive else "ℹ️"
        ctk.CTkLabel(
            container,
            text=f"{icon}  {title}",
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.DANGER_TEXT if is_destructive else Theme.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 10))

        # Message
        ctk.CTkLabel(
            container,
            text=message,
            font=accessibility_manager.get_font(13),
            text_color=Theme.TEXT_MUTED,
            justify="left",
            wraplength=360
        ).pack(anchor="w", pady=(0, 20))

        # Button row
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x")

        confirm_btn_color = Theme.DANGER_TEXT if is_destructive else Theme.PRIMARY
        confirm_btn_hover = "#991B1B" if is_destructive else Theme.PRIMARY_HOVER

        ctk.CTkButton(
            btn_row,
            text=confirm_text,
            height=38,
            fg_color=confirm_btn_color,
            hover_color=confirm_btn_hover,
            font=accessibility_manager.get_font(13, weight="bold"),
            command=self._confirm
        ).pack(side="left", expand=True, fill="x", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            height=38,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(13),
            command=self.destroy
        ).pack(side="right", padx=(8, 0))

    def _confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self.destroy()
