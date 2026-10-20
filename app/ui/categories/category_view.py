"""
Therapeutic Drug Categories Management View.
Integrated with responsive DataTable, live search, sorting, pagination, and accessible modals.
"""
import threading
from typing import Optional
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import run_in_background
from app.ui.components.badge import StatusBadge
from app.ui.components.dialogs import ConfirmDialog
from app.ui.components.data_table import DataTable


class CategoryModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, category=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.category = category
        self.on_success = on_success

        self.title("Edit Category" if category else "Register New Category")
        self.geometry("480x360")
        self.resizable(False, False)
        self.grab_set()

        self.bind("<Escape>", lambda e: self.destroy())
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
        ).pack(anchor="w", pady=(0, 2))

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
        self.entry_desc.pack(fill="x", pady=(3, 14))
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
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._save,
            font=accessibility_manager.get_font(13, weight="bold")
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel (Esc)",
            height=40,
            corner_radius=Theme.RADIUS_BUTTON,
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
            if self.category:
                return self.api_client.update_category(self.category["id"], name, desc or None)
            else:
                return self.api_client.create_category(name, desc or None)

        run_in_background(_do, on_success=lambda _: self._on_done(), on_error=self._on_err)

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
        self.categories_list = []

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
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(anchor="w")

        self.lbl_count = ctk.CTkLabel(
            title_box,
            text="Loading categories from database...",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_count.pack(anchor="w")

        # Right side action buttons
        btn_row = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=95,
            height=36,
            corner_radius=Theme.RADIUS_BUTTON,
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
            corner_radius=Theme.RADIUS_BUTTON,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._open_add_modal,
            font=accessibility_manager.get_font(12, weight="bold")
        ).pack(side="left", padx=5)

        # Search Bar Filter Row
        filter_bar = ctk.CTkFrame(self, fg_color="transparent")
        filter_bar.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Filter categories by name or clinical description...",
            height=36,
            corner_radius=Theme.RADIUS_INPUT,
            border_color=Theme.BORDER,
            font=accessibility_manager.get_font(12)
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search)

        # DataTable
        columns = [
            {"key": "name", "title": "Category Name", "weight": 2, "sortable": True},
            {"key": "description", "title": "Therapeutic Description", "weight": 3, "sortable": True},
            {
                "key": "medicines_count",
                "title": "Medicines Linked",
                "weight": 1,
                "align": "center",
                "sortable": True,
                "formatter": self._format_med_count
            }
        ]

        actions = [
            {"icon": "✏ Edit", "width": 64, "command": self._open_edit_modal},
            {"icon": "🗑 Delete", "width": 72, "fg_color": Theme.DANGER_BG, "hover_color": "#FCA5A5", "text_color": Theme.DANGER_TEXT, "command": self._prompt_delete}
        ]

        self.table = DataTable(
            self,
            columns=columns,
            actions=actions,
            page_size=10,
            empty_title="No Drug Categories Found",
            empty_desc="Click '➕ New Category' above to register your first pharmaceutical classification."
        )
        self.table.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _format_med_count(self, parent, val, row):
        count = val if val is not None else 0
        variant = "info" if count > 0 else "neutral"
        return StatusBadge(parent, text=f"{count} Items", variant=variant)

    def _open_add_modal(self):
        CategoryModal(self.winfo_toplevel(), self.api_client, on_success=self.load_categories)

    def _open_edit_modal(self, category):
        CategoryModal(self.winfo_toplevel(), self.api_client, category=category, on_success=self.load_categories)

    def _prompt_delete(self, category):
        ConfirmDialog(
            self.winfo_toplevel(),
            title=f"Delete '{category['name']}'?",
            message="Are you sure you want to delete this category? If medicines are linked, PostgreSQL foreign key constraints will block deletion.",
            confirm_text="Delete Category",
            is_destructive=True,
            on_confirm=lambda: self._execute_delete(category["id"])
        )

    def _execute_delete(self, cat_id: str):
        def _err(e):
            clean_err = str(e).replace("RuntimeError: API Error (400): ", "")
            self.lbl_count.configure(text=f"⚠️ {clean_err}", text_color=Theme.DANGER_TEXT)

        run_in_background(
            lambda: self.api_client.delete_category(cat_id),
            on_success=lambda _: self.load_categories(),
            on_error=_err
        )

    def _on_search(self, event=None):
        q = self.search_entry.get().strip().lower()
        if not q:
            self.table.set_data(self.categories_list)
        else:
            self.table.filter(lambda c: q in c["name"].lower() or (c.get("description") and q in c["description"].lower()))

    def load_categories(self):
        self.lbl_count.configure(text="⏳ Querying database via FastAPI...", text_color=Theme.TEXT_MUTED)
        run_in_background(
            lambda: self.api_client.list_categories(),
            on_success=self._render_categories,
            on_error=lambda e: self.lbl_count.configure(text=f"API Error: {e}", text_color=Theme.DANGER_TEXT)
        )

    def _render_categories(self, categories):
        self.categories_list = categories or []
        self.lbl_count.configure(
            text=f"Total: {len(self.categories_list)} registered therapeutic classifications in PostgreSQL",
            text_color=Theme.TEXT_MUTED
        )
        self.table.set_data(self.categories_list)
