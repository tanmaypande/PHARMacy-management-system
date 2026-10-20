"""
Roadmap and In-Development Feature Presentation View.
Explicitly identifies features whose backend services are pending migration,
fulfilling the strict rule: 'Do not display navigation options as functional if their underlying features do not exist.'
"""
from typing import List, Dict, Any
import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge


class RoadmapView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        module_name: str,
        icon: str,
        milestone: str,
        overview: str,
        schema_info: List[Dict[str, str]],
        planned_endpoints: List[str],
        tqm_safeguards: List[str]
    ):
        super().__init__(master, fg_color="transparent")
        self.module_name = module_name
        self.icon = icon
        self.milestone = milestone
        self.overview = overview
        self.schema_info = schema_info
        self.planned_endpoints = planned_endpoints
        self.tqm_safeguards = tqm_safeguards

        self._build_ui()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=24, pady=16)

        # 1. Top Notice Banner
        banner = ctk.CTkFrame(
            scroll,
            fg_color=Theme.BG_CARD,
            corner_radius=Theme.RADIUS_CARD,
            border_width=1,
            border_color=Theme.BORDER
        )
        banner.pack(fill="x", pady=(0, 16))

        top_row = ctk.CTkFrame(banner, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=(16, 8))

        ctk.CTkLabel(
            top_row,
            text=f"{self.icon}  {self.module_name}",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(side="left")

        StatusBadge(top_row, text=f"MILESTONE: {self.milestone}", variant="warning").pack(side="right")

        ctk.CTkLabel(
            banner,
            text=self.overview,
            font=accessibility_manager.get_font(13),
            text_color=Theme.TEXT_MUTED,
            justify="left",
            wraplength=700
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # Notice box
        notice = ctk.CTkFrame(banner, fg_color=Theme.WARNING_BG, corner_radius=8)
        notice.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            notice,
            text="⚠️ Architecture Notice: This operational module is designed in SRS.md and database architecture specs. "
                 "The frontend layout is ready, but live transaction processing remains disabled until the backend service migration is executed in Phase 2.",
            font=accessibility_manager.get_font(11),
            text_color=Theme.WARNING_TEXT,
            justify="left",
            wraplength=680
        ).pack(anchor="w", padx=14, pady=10)

        # 2. Split Cards: Data Schemas & Planned REST API Endpoints
        mid = ctk.CTkFrame(scroll, fg_color="transparent")
        mid.pack(fill="both", expand=True, pady=(0, 16))
        mid.grid_columnconfigure((0, 1), weight=1)

        # Left: Relational Schema
        schema_card = ctk.CTkFrame(mid, fg_color=Theme.BG_CARD, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER)
        schema_card.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        ctk.CTkLabel(
            schema_card,
            text="🗄️ Database Entity Schema (PostgreSQL 18)",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=16, pady=(14, 8))

        for item in self.schema_info:
            row = ctk.CTkFrame(schema_card, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text=item["table"], width=130, anchor="w", font=ctk.CTkFont(family="Consolas", size=accessibility_manager.get_font_size(11), weight="bold"), text_color=Theme.PRIMARY).pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=item["desc"], font=accessibility_manager.get_font(11), text_color=Theme.TEXT_MUTED).pack(side="left", padx=4)

        ctk.CTkLabel(schema_card, text="", height=4).pack()

        # Right: REST API Endpoints
        api_card = ctk.CTkFrame(mid, fg_color=Theme.BG_CARD, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER)
        api_card.grid(row=0, column=1, padx=(8, 0), sticky="nsew")

        ctk.CTkLabel(
            api_card,
            text="🌐 Planned RESTful API Contracts",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=16, pady=(14, 8))

        for ep in self.planned_endpoints:
            row = ctk.CTkFrame(api_card, fg_color=Theme.BG_MUTED, corner_radius=6)
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text="●", text_color=Theme.INFO_TEXT, width=16).pack(side="left", padx=(8, 2))
            ctk.CTkLabel(row, text=ep, font=ctk.CTkFont(family="Consolas", size=accessibility_manager.get_font_size(11)), text_color=Theme.TEXT_MAIN).pack(side="left", pady=6)

        ctk.CTkLabel(api_card, text="", height=4).pack()

        # 3. Bottom: TQM Quality Safeguards
        tqm_card = ctk.CTkFrame(scroll, fg_color=Theme.BG_CARD, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER)
        tqm_card.pack(fill="x")

        ctk.CTkLabel(
            tqm_card,
            text="🛡️ Quality & Poka-Yoke Controls",
            font=accessibility_manager.get_font(14, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", padx=16, pady=(14, 8))

        for g in self.tqm_safeguards:
            row = ctk.CTkFrame(tqm_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=2)
            ctk.CTkLabel(row, text="✔", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.SUCCESS_TEXT, width=20).pack(side="left")
            ctk.CTkLabel(row, text=g, font=accessibility_manager.get_font(12), text_color=Theme.TEXT_MAIN).pack(side="left", padx=6)

        ctk.CTkLabel(tqm_card, text="", height=8).pack()
