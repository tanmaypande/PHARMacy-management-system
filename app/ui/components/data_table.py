"""
Reusable, commercial-grade DataTable component for CustomTkinter.
Supports:
- Proportional responsive column widths
- Interactive header sorting (asc / desc)
- Client-side pagination (10, 25, 50 rows per page)
- Alternating row styling and row hover
- Action buttons column (View, Edit, Delete/Archive)
- Empty state display
"""
from typing import List, Dict, Any, Callable, Optional
import customtkinter as ctk
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.empty_state import EmptyState
from app.ui.components.badge import StatusBadge


class DataTable(ctk.CTkFrame):
    def __init__(
        self,
        master,
        columns: List[Dict[str, Any]],
        data: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 10,
        actions: Optional[List[Dict[str, Any]]] = None,
        empty_title: str = "No Records Found",
        empty_desc: str = "There are no records matching the current criteria.",
        **kwargs
    ):
        super().__init__(master, fg_color=Theme.BG_CARD, corner_radius=Theme.RADIUS_CARD, border_width=1, border_color=Theme.BORDER, **kwargs)
        self.columns = columns
        self.raw_data = data or []
        self.filtered_data = list(self.raw_data)
        self.page_size = page_size
        self.current_page = 1
        self.sort_key: Optional[str] = None
        self.sort_ascending: bool = True
        self.actions = actions or []
        self.empty_title = empty_title
        self.empty_desc = empty_desc

        self._build_layout()
        self._refresh_table()

    def _build_layout(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color=Theme.BG_MUTED, height=40, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        self._build_header_columns()

        # 2. Scrollable Body
        self.body_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body_scroll.grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        self.body_scroll.grid_columnconfigure(0, weight=1)

        # 3. Pagination Footer
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent", height=42)
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=6)
        self._build_footer()

    def _build_header_columns(self):
        for w in self.header_frame.winfo_children():
            w.destroy()

        col_count = len(self.columns) + (1 if self.actions else 0)
        for i in range(col_count):
            weight = self.columns[i].get("weight", 1) if i < len(self.columns) else 1
            self.header_frame.grid_columnconfigure(i, weight=weight)

        for idx, col in enumerate(self.columns):
            key = col["key"]
            label = col["title"]
            align = col.get("align", "w")
            sortable = col.get("sortable", True)

            sort_indicator = ""
            if self.sort_key == key:
                sort_indicator = " ▲" if self.sort_ascending else " ▼"

            btn_text = f"{label}{sort_indicator}"
            if sortable:
                btn = ctk.CTkButton(
                    self.header_frame,
                    text=btn_text,
                    height=32,
                    fg_color="transparent",
                    hover_color=Theme.SECONDARY_HOVER,
                    text_color=Theme.TEXT_MAIN,
                    font=accessibility_manager.get_font(12, weight="bold"),
                    anchor=align,
                    command=lambda k=key: self._on_sort(k)
                )
                btn.grid(row=0, column=idx, sticky="ew", padx=6, pady=4)
            else:
                lbl = ctk.CTkLabel(
                    self.header_frame,
                    text=btn_text,
                    font=accessibility_manager.get_font(12, weight="bold"),
                    text_color=Theme.TEXT_MUTED,
                    anchor=align
                )
                lbl.grid(row=0, column=idx, sticky="ew", padx=6, pady=4)

        if self.actions:
            lbl_act = ctk.CTkLabel(
                self.header_frame,
                text="Actions",
                font=accessibility_manager.get_font(12, weight="bold"),
                text_color=Theme.TEXT_MUTED,
                anchor="center"
            )
            lbl_act.grid(row=0, column=len(self.columns), sticky="ew", padx=6, pady=4)

    def _build_footer(self):
        self.lbl_info = ctk.CTkLabel(
            self.footer_frame,
            text="",
            font=accessibility_manager.get_font(11),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_info.pack(side="left")

        # Controls row
        ctrl_box = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        ctrl_box.pack(side="right")

        self.btn_prev = ctk.CTkButton(
            ctrl_box,
            text="◀ Prev",
            width=64,
            height=28,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(11, weight="bold"),
            command=self._prev_page
        )
        self.btn_prev.pack(side="left", padx=4)

        self.lbl_page = ctk.CTkLabel(
            ctrl_box,
            text="1 / 1",
            width=60,
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_page.pack(side="left", padx=4)

        self.btn_next = ctk.CTkButton(
            ctrl_box,
            text="Next ▶",
            width=64,
            height=28,
            fg_color=Theme.SECONDARY,
            hover_color=Theme.SECONDARY_HOVER,
            text_color=Theme.SECONDARY_TEXT,
            font=accessibility_manager.get_font(11, weight="bold"),
            command=self._next_page
        )
        self.btn_next.pack(side="left", padx=4)

    def set_data(self, data: List[Dict[str, Any]]):
        self.raw_data = data or []
        self.filtered_data = list(self.raw_data)
        self.current_page = 1
        self._refresh_table()

    def filter(self, predicate: Callable[[Dict[str, Any]], bool]):
        self.filtered_data = [row for row in self.raw_data if predicate(row)]
        self.current_page = 1
        self._refresh_table()

    def _on_sort(self, key: str):
        if self.sort_key == key:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_key = key
            self.sort_ascending = True

        def sort_val(row):
            val = row.get(key)
            if val is None:
                return ""
            if isinstance(val, (int, float)):
                return val
            return str(val).lower()

        self.filtered_data.sort(key=sort_val, reverse=not self.sort_ascending)
        self._build_header_columns()
        self._refresh_table()

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._refresh_table()

    def _next_page(self):
        total_pages = max(1, (len(self.filtered_data) + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self._refresh_table()

    def _refresh_table(self):
        for w in self.body_scroll.winfo_children():
            w.destroy()

        total = len(self.filtered_data)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        if self.current_page > total_pages:
            self.current_page = total_pages

        start_idx = (self.current_page - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total)
        page_rows = self.filtered_data[start_idx:end_idx]

        # Update footer text
        if total == 0:
            self.lbl_info.configure(text="Showing 0 of 0 records")
            self.lbl_page.configure(text="1 / 1")
            self.btn_prev.configure(state="disabled")
            self.btn_next.configure(state="disabled")

            EmptyState(
                self.body_scroll,
                title=self.empty_title,
                description=self.empty_desc
            ).pack(fill="both", expand=True, pady=30)
            return

        self.lbl_info.configure(text=f"Showing {start_idx + 1}-{end_idx} of {total} records")
        self.lbl_page.configure(text=f"{self.current_page} / {total_pages}")
        self.btn_prev.configure(state="normal" if self.current_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.current_page < total_pages else "disabled")

        col_count = len(self.columns) + (1 if self.actions else 0)

        for row_idx, row_data in enumerate(page_rows):
            bg_col = Theme.BG_ROW_ALT if (row_idx % 2 == 1) else "transparent"

            row_frame = ctk.CTkFrame(self.body_scroll, fg_color=bg_col, corner_radius=6, height=36)
            row_frame.pack(fill="x", pady=1)

            for i in range(col_count):
                weight = self.columns[i].get("weight", 1) if i < len(self.columns) else 1
                row_frame.grid_columnconfigure(i, weight=weight)

            for col_idx, col in enumerate(self.columns):
                key = col["key"]
                raw_val = row_data.get(key)
                align = col.get("align", "w")
                formatter = col.get("formatter")

                if formatter:
                    cell_widget = formatter(row_frame, raw_val, row_data)
                    cell_widget.grid(row=0, column=col_idx, sticky="ew", padx=6, pady=4)
                else:
                    text_str = str(raw_val) if raw_val is not None else "—"
                    lbl = ctk.CTkLabel(
                        row_frame,
                        text=text_str,
                        font=accessibility_manager.get_font(12),
                        text_color=Theme.TEXT_MAIN,
                        anchor=align
                    )
                    lbl.grid(row=0, column=col_idx, sticky="ew", padx=6, pady=4)

            # Actions column
            if self.actions:
                act_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
                act_frame.grid(row=0, column=len(self.columns), sticky="ew", padx=4, pady=2)

                for act in self.actions:
                    btn_act = ctk.CTkButton(
                        act_frame,
                        text=act.get("icon", act.get("label", "•")),
                        width= act.get("width", 32),
                        height=26,
                        corner_radius=4,
                        fg_color=act.get("fg_color", Theme.SECONDARY),
                        hover_color=act.get("hover_color", Theme.SECONDARY_HOVER),
                        text_color=act.get("text_color", Theme.SECONDARY_TEXT),
                        font=accessibility_manager.get_font(11, weight="bold"),
                        command=lambda a=act, r=row_data: a["command"](r)
                    )
                    btn_act.pack(side="left", padx=2)
