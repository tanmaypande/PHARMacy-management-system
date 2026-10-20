import threading
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.badge import StatusBadge
from app.ui.components.empty_state import EmptyState
from app.ui.components.dialogs import ConfirmDialog


class CategoryModal(ctk.CTkToplevel):
    """
    Polished modal dialog for creating or updating drug categories.
    """
    def __init__(self, master, api_client: APIClient, category=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.category = category
        self.on_success = on_success

        self.title("Edit Category" if category else "Add Drug Category")
        self.geometry("460x340")
        self.resizable(False, False)
        self.grab_set()

        self._build_form()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=28, pady=22)

        title_text = "Edit Category Details" if self.category else "Register New Drug Category"
        ctk.CTkLabel(
            container,
            text=title_text,
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            container,
            text="Groups medicines for therapeutic classification and inventory analytics",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(anchor="w", pady=(0, 16))

        # Category Name
        ctk.CTkLabel(container, text="Category Name *", font=accessibility_manager.get_font(13, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(
            container,
            placeholder_text="e.g. Analgesics, Antibiotics, Antipyretics",
            height=38,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(13)
        )
        self.entry_name.pack(fill="x", pady=(3, 12))
        if self.category:
            self.entry_name.insert(0, self.category.get("name", ""))

        # Description
        ctk.CTkLabel(container, text="Therapeutic Description (Optional)", font=accessibility_manager.get_font(13), text_color=Theme.TEXT_MAIN).pack(anchor="w")
        self.entry_desc = ctk.CTkEntry(
            container,
            placeholder_text="Clinical indications or pharmacologic class notes",
            height=38,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(13)
        )
        self.entry_desc.pack(fill="x", pady=(3, 16))
        if self.category and self.category.get("description"):
            self.entry_desc.insert(0, self.category.get("description", ""))

        self.lbl_error = ctk.CTkLabel(container, text="", text_color=Theme.DANGER_TEXT, font=accessibility_manager.get_font(12))
        self.lbl_error.pack(anchor="w", pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="Save Category",
            height=40,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._save,
            font=accessibility_manager.get_font(13, weight="bold")
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            height=40,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            command=self.destroy,
            font=accessibility_manager.get_font(13)
        ).pack(side="right", padx=(10, 0))

    def _save(self):
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip()
        if not name:
            self.lbl_error.configure(text="Category name is required.")
            return

        self.btn_save.configure(state="disabled", text="Saving...")
        self.lbl_error.configure(text="")

        def _do():
            try:
                if self.category:
                    self.api_client.update_category(self.category["id"], name, desc or None)
                else:
                    self.api_client.create_category(name, desc or None)
                self.after(0, self._on_done)
            except Exception as e:
                self.after(0, self._on_err, str(e))

        threading.Thread(target=_do, daemon=True).start()

    def _on_done(self):
        if self.on_success:
            self.on_success()
        self.destroy()

    def _on_err(self, msg: str):
        self.btn_save.configure(state="normal", text="Save Category")
        clean_msg = msg.replace("RuntimeError: ", "")
        self.lbl_error.configure(text=clean_msg)


class CategoryView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self._build_ui()
        self.load_categories()

    def _build_ui(self):
        # Action Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(15, 10))

        title_box = ctk.CTkFrame(toolbar, fg_color="transparent")
        title_box.pack(side="left")

        ctk.CTkLabel(
            title_box,
            text="🗂 Drug Classification & Categories",
            font=accessibility_manager.get_font(20, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.count_badge = ctk.CTkLabel(
            title_box,
            text="Loading categories...",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.count_badge.pack(anchor="w")

        btn_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=95,
            height=36,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            command=self.load_categories,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ New Category",
            width=140,
            height=36,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_add_modal,
            font=accessibility_manager.get_font(13, weight="bold")
        ).pack(side="left", padx=5)

        # Table Container
        self.table_card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        self.table_card.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        # Table Header
        self.hdr = ctk.CTkFrame(self.table_card, fg_color=Theme.BG_MUTED, height=40, corner_radius=8)
        self.hdr.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(self.hdr, text="CATEGORY NAME", width=220, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=12)
        ctk.CTkLabel(self.hdr, text="THERAPEUTIC DESCRIPTION", width=340, anchor="w", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=12)
        ctk.CTkLabel(self.hdr, text="MEDICINES LINKED", width=120, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=12)
        ctk.CTkLabel(self.hdr, text="ACTIONS", width=140, anchor="center", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MUTED).pack(side="left", padx=12)

        # Scrollable rows area
        self.table_scroll = ctk.CTkScrollableFrame(self.table_card, fg_color="transparent")
        self.table_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _open_add_modal(self):
        CategoryModal(self, self.api_client, on_success=self.load_categories)

    def _open_edit_modal(self, category):
        CategoryModal(self, self.api_client, category=category, on_success=self.load_categories)

    def load_categories(self):
        self.count_badge.configure(text="⏳ Querying database via FastAPI...")

        def _fetch():
            try:
                categories = self.api_client.list_categories()
                self.after(0, self._render_categories, categories)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_categories(self, categories):
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        total = len(categories)
        self.count_badge.configure(text=f"Total: {total} registered classifications in catalog")

        if not categories:
            EmptyState(
                self.table_scroll,
                icon="🗂",
                title="No Drug Categories Registered",
                description="Create therapeutic categories to organize medications and manage stock.",
                action_text="➕ Register First Category",
                action_command=self._open_add_modal
            ).pack(fill="both", expand=True, pady=30)
            return

        for idx, cat in enumerate(categories):
            # Alternating row background for enhanced legibility
            row_bg = "transparent" if idx % 2 == 0 else Theme.BG_MUTED
            row = ctk.CTkFrame(self.table_scroll, fg_color=row_bg, corner_radius=6, height=42)
            row.pack(fill="x", pady=2)

            # Name with brand indicator
            ctk.CTkLabel(
                row,
                text=cat["name"],
                width=220,
                anchor="w",
                font=accessibility_manager.get_font(13, weight="bold"),
                text_color=Theme.TEXT_MAIN
            ).pack(side="left", padx=12)

            # Description
            ctk.CTkLabel(
                row,
                text=cat.get("description") or "—",
                width=340,
                anchor="w",
                font=accessibility_manager.get_font(12),
                text_color=Theme.TEXT_MUTED
            ).pack(side="left", padx=12)

            # Linked medicines count badge
            m_count = cat.get("medicine_count", 0)
            count_box = ctk.CTkFrame(row, fg_color="transparent", width=120)
            count_box.pack(side="left", padx=12)
            StatusBadge(count_box, text=f"{m_count} Items", variant="info" if m_count > 0 else "neutral").pack(expand=True)

            # Actions
            act_frame = ctk.CTkFrame(row, fg_color="transparent", width=140)
            act_frame.pack(side="left", padx=12)

            ctk.CTkButton(
                act_frame,
                text="✏️ Edit",
                width=60,
                height=28,
                fg_color=Theme.SECONDARY,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.SECONDARY_TEXT,
                command=lambda c=cat: self._open_edit_modal(c),
                font=accessibility_manager.get_font(11, weight="bold")
            ).pack(side="left", padx=3)

            ctk.CTkButton(
                act_frame,
                text="🗑️",
                width=35,
                height=28,
                fg_color="#FEE2E2",
                hover_color="#FCA5A5",
                text_color="#B91C1C",
                command=lambda c=cat: self._confirm_delete(c),
                font=accessibility_manager.get_font(11)
            ).pack(side="left", padx=3)

    def _confirm_delete(self, cat):
        if cat.get("medicine_count", 0) > 0:
            ConfirmDialog(
                self,
                title="Cannot Delete Category",
                message=f"Category '{cat['name']}' currently contains {cat['medicine_count']} active medicine(s).\n\n"
                        f"TQM Integrity Safeguard: Reassign or delete linked medicines first before deleting this category.",
                confirm_text="Understood",
                is_destructive=False
            )
            return

        ConfirmDialog(
            self,
            title="Delete Category",
            message=f"Are you sure you want to permanently delete category '{cat['name']}'?",
            confirm_text="Delete Category",
            is_destructive=True,
            on_confirm=lambda: self._execute_delete(cat["id"])
        )

    def _execute_delete(self, cat_id):
        def _do():
            try:
                self.api_client.delete_category(cat_id)
                self.after(0, self.load_categories)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_do, daemon=True).start()

    def _render_error(self, err_msg):
        self.count_badge.configure(text=f"Error: {err_msg}", text_color=Theme.DANGER_TEXT)
