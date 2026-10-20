import customtkinter as ctk
from app.ui.accessibility.accessibility_manager import accessibility_manager


class ComingSoonView(ctk.CTkFrame):
    def __init__(self, master, module_name: str, sprint_info: str = "Scheduled in next sprint milestone"):
        super().__init__(master, fg_color="transparent")
        self.module_name = module_name
        self.sprint_info = sprint_info
        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=accessibility_manager.get_card_fg(), corner_radius=12)
        container.pack(expand=True, padx=40, pady=40)

        icon_label = ctk.CTkLabel(
            container,
            text="🚧",
            font=ctk.CTkFont(size=accessibility_manager.get_font_size(48))
        )
        icon_label.pack(pady=(30, 10))

        title = ctk.CTkLabel(
            container,
            text=f"{self.module_name} Module",
            font=accessibility_manager.get_font(22, weight="bold")
        )
        title.pack(padx=30, pady=(0, 10))

        desc = ctk.CTkLabel(
            container,
            text=f"The {self.module_name} feature is fully designed in our architecture specification.\n"
                 f"Status: {self.sprint_info}.\n"
                 f"The core Category, Medicine, and Batch Inventory vertical slices are active.",
            font=accessibility_manager.get_font(14),
            text_color="#94A3B8"
        )
        desc.pack(padx=30, pady=(0, 30))
