import threading
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.accessibility.accessibility_manager import accessibility_manager


class CategoryModal(ctk.CTkToplevel):
    def __init__(self, master, api_client: APIClient, category=None, on_success=None):
        super().__init__(master)
        self.api_client = api_client
        self.category = category
        self.on_success = on_success

        self.title("Edit Category" if category else "Add New Category")
        self.geometry("440x320")
        self.resizable(False, False)
        self.grab_set()

        self._build_form()

    def _build_form(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=25, pady=20)

        title_text = "Edit Drug Category" if self.category else "Create Drug Category"
        ctk.CTkLabel(
            container,
            text=title_text,
            font=accessibility_manager.get_font(18, weight="bold")
        ).pack(anchor="w", pady=(0, 15))

        # Name Field
        ctk.CTkLabel(container, text="Category Name *", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.entry_name = ctk.CTkEntry(
            container,
            placeholder_text="e.g. Analgesics, Antibiotics, Antipyretics",
            height=36,
            font=accessibility_manager.get_font(13)
        )
        self.entry_name.pack(fill="x", pady=(3, 12))
        if self.category:
            self.entry_name.insert(0, self.category.get("name", ""))

        # Description Field
        ctk.CTkLabel(container, text="Description (Optional)", font=accessibility_manager.get_font(13)).pack(anchor="w")
        self.entry_desc = ctk.CTkEntry(
            container,
            placeholder_text="Clinical notes or therapeutic class",
            height=36,
            font=accessibility_manager.get_font(13)
        )
        self.entry_desc.pack(fill="x", pady=(3, 15))
        if self.category and self.category.get("description"):
            self.entry_desc.insert(0, self.category.get("description", ""))

        self.lbl_error = ctk.CTkLabel(container, text="", text_color="#EF4444", font=accessibility_manager.get_font(12))
        self.lbl_error.pack(anchor="w", pady=(0, 10))

        # Buttons
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="Save Category",
            height=38,
            command=self._save,
            font=accessibility_manager.get_font(13, weight="bold")
        )
        self.btn_save.pack(side="left", expand=True, fill="x", padx=(0, 10))

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            height=38,
            fg_color="#64748B",
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
        self.lbl_error.configure(text=msg.replace("RuntimeError: ", ""))


class CategoryView(ctk.CTkFrame):
    def __init__(self, master, api_client: APIClient):
        super().__init__(master, fg_color="transparent")
        self.api_client = api_client
        self._build_ui()
        self.load_categories()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 10))

        ctk.CTkLabel(
            header,
            text="🗂 Drug Category Management",
            font=accessibility_manager.get_font(20, weight="bold")
        ).pack(side="left")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="🔄 Refresh",
            width=90,
            command=self.load_categories,
            font=accessibility_manager.get_font(13)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_row,
            text="➕ Add Category",
            width=130,
            fg_color="#10B981",
            hover_color="#059669",
            command=self._open_add_modal,
            font=accessibility_manager.get_font(13, weight="bold")
        ).pack(side="left", padx=5)

        # Status text
        self.status_lbl = ctk.CTkLabel(self, text="Loading categories...", font=accessibility_manager.get_font(13), text_color="#94A3B8")
        self.status_lbl.pack(anchor="w", padx=20, pady=(0, 5))

        # Scrollable table container
        self.table_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=accessibility_manager.get_card_fg(),
            corner_radius=10
        )
        self.table_scroll.pack(fill="both", expand=True, padx=20, pady=(5, 20))

    def _open_add_modal(self):
        CategoryModal(self, self.api_client, on_success=self.load_categories)

    def _open_edit_modal(self, category):
        CategoryModal(self, self.api_client, category=category, on_success=self.load_categories)

    def load_categories(self):
        self.status_lbl.configure(text="⏳ Fetching categories from backend...", text_color="#FBBF24")

        def _fetch():
            try:
                categories = self.api_client.list_categories()
                self.after(0, self._render_categories, categories)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def _render_categories(self, categories):
        # Clear existing
        for widget in self.table_scroll.winfo_children():
            widget.destroy()

        self.status_lbl.configure(text=f"Showing {len(categories)} categories", text_color="#34D399")

        if not categories:
            ctk.CTkLabel(
                self.table_scroll,
                text="No drug categories found. Click '➕ Add Category' to create the first one.",
                font=accessibility_manager.get_font(14)
            ).pack(pady=40)
            return

        # Header Row
        hdr = ctk.CTkFrame(self.table_scroll, fg_color="#334155", height=36)
        hdr.pack(fill="x", padx=5, pady=5)
        ctk.CTkLabel(hdr, text="Category Name", width=180, anchor="w", font=accessibility_manager.get_font(13, weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Description", width=260, anchor="w", font=accessibility_manager.get_font(13, weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Medicines", width=80, anchor="center", font=accessibility_manager.get_font(13, weight="bold")).pack(side="left", padx=10)
        ctk.CTkLabel(hdr, text="Actions", width=140, anchor="center", font=accessibility_manager.get_font(13, weight="bold")).pack(side="left", padx=10)

        for cat in categories:
            row = ctk.CTkFrame(self.table_scroll, fg_color="transparent")
            row.pack(fill="x", padx=5, pady=4)

            ctk.CTkLabel(row, text=cat["name"], width=180, anchor="w", font=accessibility_manager.get_font(13, weight="bold")).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=cat.get("description") or "—", width=260, anchor="w", font=accessibility_manager.get_font(13), text_color="#94A3B8").pack(side="left", padx=10)
            
            # Badge count
            m_count = cat.get("medicine_count", 0)
            count_lbl = ctk.CTkLabel(row, text=str(m_count), width=80, anchor="center", font=accessibility_manager.get_font(13))
            count_lbl.pack(side="left", padx=10)

            act_frame = ctk.CTkFrame(row, fg_color="transparent", width=140)
            act_frame.pack(side="left", padx=10)

            ctk.CTkButton(
                act_frame,
                text="✏️ Edit",
                width=60,
                height=28,
                command=lambda c=cat: self._open_edit_modal(c),
                font=accessibility_manager.get_font(11)
            ).pack(side="left", padx=3)

            ctk.CTkButton(
                act_frame,
                text="🗑️ Delete",
                width=60,
                height=28,
                fg_color="#EF4444",
                hover_color="#DC2626",
                command=lambda c=cat: self._delete_category(c),
                font=accessibility_manager.get_font(11)
            ).pack(side="left", padx=3)

    def _delete_category(self, cat):
        if cat.get("medicine_count", 0) > 0:
            self.status_lbl.configure(
                text=f"❌ Cannot delete '{cat['name']}': Contains {cat['medicine_count']} active medicines.",
                text_color="#EF4444"
            )
            return

        def _do():
            try:
                self.api_client.delete_category(cat["id"])
                self.after(0, self.load_categories)
            except Exception as e:
                self.after(0, self._render_error, str(e))

        threading.Thread(target=_do, daemon=True).start()

    def _render_error(self, err_msg):
        self.status_lbl.configure(text=f"Error: {err_msg}", text_color="#EF4444")
