import threading
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.dashboard.dashboard_view import DashboardView
from app.ui.categories.category_view import CategoryView
from app.ui.medicines.medicine_view import MedicineView
from app.ui.inventory.inventory_view import InventoryView
from app.ui.settings.settings_view import SettingsView
from app.ui.common.coming_soon_view import ComingSoonView


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Pharmacy Management System — Commercial & TQM Q12 Edition")
        self.geometry("1100x700")
        self.minsize(950, 600)

        # Isolated API Client
        self.api_client = APIClient(base_url="http://127.0.0.1:8000")
        self.current_view_key = "dashboard"
        self.current_view_widget = None

        # Subscribe to accessibility updates
        accessibility_manager.subscribe(self._on_accessibility_change)

        self._build_layout()
        self.navigate("dashboard")
        self._start_connection_monitor()

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= Sidebar =================
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(11, weight=1)  # Spacer pushes status pill to bottom

        # Brand / Title
        self.lbl_logo = ctk.CTkLabel(
            self.sidebar,
            text="🏥 MediCare PMS",
            font=accessibility_manager.get_font(18, weight="bold")
        )
        self.lbl_logo.grid(row=0, column=0, padx=20, pady=(20, 2), sticky="w")

        self.lbl_sub = ctk.CTkLabel(
            self.sidebar,
            text="TQM Quality & Q12 Standards",
            font=accessibility_manager.get_font(11, slant="italic"),
            text_color="#94A3B8"
        )
        self.lbl_sub.grid(row=1, column=0, padx=20, pady=(0, 15), sticky="w")

        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊  Dashboard"),
            ("medicines", "💊  Medicines"),
            ("categories", "🗂  Categories"),
            ("inventory", "📦  Inventory Batches"),
            ("billing", "🧾  Billing & POS"),
            ("suppliers", "🏢  Suppliers"),
            ("purchases", "🛒  Purchases"),
            ("reports", "📈  TQM Reports"),
            ("users", "👥  User Accounts"),
            ("settings", "⚙  Accessibility Settings")
        ]

        for idx, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                height=36,
                corner_radius=8,
                anchor="w",
                fg_color="transparent",
                text_color="#F8FAFC",
                hover_color="#334155",
                font=accessibility_manager.get_font(13),
                command=lambda k=key: self.navigate(k)
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

        # Bottom Connection Status Pill
        self.status_pill = ctk.CTkFrame(self.sidebar, fg_color="#1E293B", corner_radius=8)
        self.status_pill.grid(row=12, column=0, padx=12, pady=15, sticky="ew")

        self.status_dot = ctk.CTkLabel(
            self.status_pill,
            text="⏳ Checking API...",
            font=accessibility_manager.get_font(11),
            text_color="#FBBF24"
        )
        self.status_dot.pack(padx=10, pady=8)

        # ================= Main View Container =================
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

    def navigate(self, key: str):
        self.current_view_key = key

        # Update button highlights
        accent_color = accessibility_manager.get_accent_color()
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=accent_color, text_color="#FFFFFF" if accent_color != "#FACC15" else "#000000")
            else:
                btn.configure(fg_color="transparent", text_color="#F8FAFC")

        # Destroy old view
        if self.current_view_widget:
            self.current_view_widget.destroy()

        # Instantiate new view
        if key == "dashboard":
            self.current_view_widget = DashboardView(self.main_container, self.api_client, on_navigate=self.navigate)
        elif key == "medicines":
            self.current_view_widget = MedicineView(self.main_container, self.api_client)
        elif key == "categories":
            self.current_view_widget = CategoryView(self.main_container, self.api_client)
        elif key == "inventory":
            self.current_view_widget = InventoryView(self.main_container, self.api_client)
        elif key == "settings":
            self.current_view_widget = SettingsView(self.main_container, on_theme_change=self._on_accessibility_change)
        elif key == "billing":
            self.current_view_widget = ComingSoonView(self.main_container, "Point of Sale & Billing", "Phase 2 Sprint")
        elif key == "suppliers":
            self.current_view_widget = ComingSoonView(self.main_container, "Wholesale Suppliers", "Phase 2 Sprint")
        elif key == "purchases":
            self.current_view_widget = ComingSoonView(self.main_container, "Purchase Orders", "Phase 2 Sprint")
        elif key == "reports":
            self.current_view_widget = ComingSoonView(self.main_container, "TQM Pareto & Defect Analytics", "Phase 2 Sprint")
        elif key == "users":
            self.current_view_widget = ComingSoonView(self.main_container, "Role-Based User Security", "Phase 2 Sprint")

        self.current_view_widget.grid(row=0, column=0, sticky="nsew")

    def _start_connection_monitor(self):
        def _check():
            health = self.api_client.get_health()
            self.after(0, self._render_health, health)

        threading.Thread(target=_check, daemon=True).start()

    def _render_health(self, health: dict):
        api_ok = health.get("api_service") == "running"
        db_ok = health.get("database", {}).get("database_connected", False)

        if api_ok and db_ok:
            self.status_dot.configure(text="● API & DB Online", text_color="#34D399")
        elif api_ok and not db_ok:
            self.status_dot.configure(text="● DB Degraded", text_color="#F87171")
        else:
            self.status_dot.configure(text="● Backend Offline", text_color="#EF4444")

    def _on_accessibility_change(self):
        # Refresh current view to apply font scaling and contrast changes
        self.navigate(self.current_view_key)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
