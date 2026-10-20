import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge


class ComingSoonView(ctk.CTkFrame):
    """
    Polished placeholder view for roadmap modules (Sales/Billing, Purchases, Suppliers, Customers, Reports).
    Presents planned architectural capabilities, TQM quality safeguards, and database schema status.
    """
    def __init__(
        self,
        master,
        module_name: str,
        sprint_info: str = "Phase 2 Engineering Milestone",
        icon: str = "📋",
        features: list = None
    ):
        super().__init__(master, fg_color="transparent")
        self.module_name = module_name
        self.sprint_info = sprint_info
        self.icon = icon
        self.features = features or [
            "Full RESTful API endpoints and Pydantic validation schemas planned",
            "PostgreSQL 18 transactional integrity and audit logging",
            "CustomTkinter responsive view with accessible focus states",
            "Strict separation: UI -> HTTP API -> Service -> Repository -> Database"
        ]
        self._build_ui()

    def _build_ui(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(expand=True, fill="both", padx=30, pady=24)

        card = ctk.CTkFrame(
            wrapper,
            fg_color=Theme.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER
        )
        card.pack(expand=True, fill="both", padx=20, pady=10)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(expand=True, pady=40, padx=40)

        # Module Icon
        ctk.CTkLabel(
            inner,
            text=self.icon,
            font=ctk.CTkFont(size=accessibility_manager.get_font_size(44))
        ).pack(pady=(0, 10))

        # Title
        ctk.CTkLabel(
            inner,
            text=f"{self.module_name}",
            font=accessibility_manager.get_font(22, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(pady=(0, 6))

        # Status Badge
        StatusBadge(inner, text=f"🚀 {self.sprint_info}", variant="info").pack(pady=(0, 16))

        # Description
        ctk.CTkLabel(
            inner,
            text=f"The {self.module_name} module architecture, database models, and workflows are specified in SRS.md.\n"
                 "The current active sprint has completed the Category, Medicine, and Batch Inventory vertical slices.",
            font=accessibility_manager.get_font(13),
            text_color=Theme.TEXT_MUTED,
            justify="center"
        ).pack(pady=(0, 24))

        # Features Checklist
        feat_card = ctk.CTkFrame(inner, fg_color=Theme.BG_MUTED, corner_radius=10)
        feat_card.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            feat_card,
            text="Planned Capabilities & Quality Safeguards:",
            font=accessibility_manager.get_font(12, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=16, pady=(12, 6))

        for feat in self.features:
            row = ctk.CTkFrame(feat_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(
                row,
                text="✔",
                font=accessibility_manager.get_font(12, weight="bold"),
                text_color=Theme.SUCCESS_TEXT,
                width=20
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=feat,
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=6)

        ctk.CTkLabel(feat_card, text="", height=4).pack()
