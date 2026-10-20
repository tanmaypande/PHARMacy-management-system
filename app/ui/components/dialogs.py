"""
Accessible dialogs and modals for MediCare Pharmacy Management System.
Includes:
- ConfirmDialog for destructive or critical actions
- AlertsModal for review of low-stock and expiry warnings
- DetailModal for comprehensive item inspection
"""
import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge


class ConfirmDialog(ctk.CTkToplevel):
    """
    Accessible confirmation modal for destructive or critical actions.
    Supports Escape key to dismiss.
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
        self.geometry("440x230")
        self.resizable(False, False)
        self.grab_set()

        # Keyboard accessibility: Escape to cancel
        self.bind("<Escape>", lambda e: self.destroy())

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
            wraplength=380
        ).pack(anchor="w", pady=(0, 20))

        # Button row
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x")

        confirm_btn_color = Theme.DANGER_TEXT if is_destructive else Theme.PRIMARY
        confirm_btn_hover = "#991B1B" if is_destructive else Theme.PRIMARY_HOVER

        self.btn_confirm = ctk.CTkButton(
            btn_row,
            text=confirm_text,
            height=38,
            fg_color=confirm_btn_color,
            hover_color=confirm_btn_hover,
            font=accessibility_manager.get_font(13, weight="bold"),
            command=self._confirm
        )
        self.btn_confirm.pack(side="left", expand=True, fill="x", padx=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            btn_row,
            text="Cancel (Esc)",
            height=38,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(13),
            command=self.destroy
        )
        self.btn_cancel.pack(side="right", padx=(8, 0))

    def _confirm(self):
        if self.on_confirm:
            self.on_confirm()
        self.destroy()


class AlertsModal(ctk.CTkToplevel):
    """
    Accessible Notification and Operational Alerts Modal.
    Lists critical inventory, expiration, and database integrity notices.
    """
    def __init__(self, master, alerts: list = None, on_navigate=None):
        super().__init__(master)
        self.alerts = alerts or []
        self.on_navigate = on_navigate

        self.title("Clinical Alerts & Quality Notifications")
        self.geometry("540x480")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Header
        hdr = ctk.CTkFrame(container, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            hdr,
            text="🔔 Clinical Alerts & Quality Safeguards",
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        ctk.CTkLabel(
            hdr,
            text=f"{len(self.alerts)} Total Alerts",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(side="right")

        # Scrollable alerts list
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, pady=(0, 14))

        if not self.alerts:
            ctk.CTkLabel(
                scroll,
                text="✅ All clinical safeguards clear. No pending stock or expiry alerts.",
                font=accessibility_manager.get_font(13),
                text_color=Theme.SUCCESS_TEXT
            ).pack(pady=40)
        else:
            for item in self.alerts:
                card = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER)
                card.pack(fill="x", pady=4)

                top = ctk.CTkFrame(card, fg_color="transparent")
                top.pack(fill="x", padx=12, pady=(10, 2))

                variant = item.get("variant", "warning")
                StatusBadge(top, text=item.get("badge", "ALERT"), variant=variant).pack(side="left")

                ctk.CTkLabel(
                    top,
                    text=item.get("title", "Alert"),
                    font=accessibility_manager.get_font(13, weight="bold"),
                    text_color=Theme.TEXT_MAIN
                ).pack(side="left", padx=8)

                desc = ctk.CTkLabel(
                    card,
                    text=item.get("message", ""),
                    font=accessibility_manager.get_font(11),
                    text_color=Theme.TEXT_MUTED,
                    justify="left",
                    wraplength=480
                )
                desc.pack(anchor="w", padx=12, pady=(0, 10))

        # Close button
        ctk.CTkButton(
            container,
            text="Close (Esc)",
            height=36,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(12, weight="bold"),
            command=self.destroy
        ).pack(fill="x")


class DetailModal(ctk.CTkToplevel):
    """
    Key-Value Inspector Modal for viewing details of any Medicine or Batch.
    """
    def __init__(self, master, title: str, subtitle: str, data_dict: dict):
        super().__init__(master)
        self.title(title)
        self.geometry("500x460")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        # Title
        ctk.CTkLabel(
            container,
            text=title,
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        ctk.CTkLabel(
            container,
            text=subtitle,
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # Key-Value Grid inside scroll
        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, pady=(0, 14))

        for k, v in data_dict.items():
            row = ctk.CTkFrame(scroll, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=k,
                width=160,
                anchor="w",
                font=accessibility_manager.get_font(12, weight="bold"),
                text_color=Theme.TEXT_MUTED
            ).pack(side="left", padx=12, pady=8)

            ctk.CTkLabel(
                row,
                text=str(v) if v is not None else "—",
                anchor="w",
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=6, pady=8)

        ctk.CTkButton(
            container,
            text="Close (Esc)",
            height=36,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(12, weight="bold"),
            command=self.destroy
        ).pack(fill="x")
