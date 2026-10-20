import threading
import time
import customtkinter as ctk
from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.components.header import TopHeader
from app.ui.dashboard.dashboard_view import DashboardView
from app.ui.categories.category_view import CategoryView
from app.ui.medicines.medicine_view import MedicineView
from app.ui.inventory.inventory_view import InventoryView
from app.ui.settings.settings_view import SettingsView
from app.ui.common.coming_soon_view import ComingSoonView


class MainWindow(ctk.CTk):
    """
    Polished Healthcare SaaS Desktop Main Window.
    Implements:
    - Fixed left sidebar with 10 clinical and administrative modules
    - Top header bar with real-time health indicator, theme toggle, and user profile
    - Seamless view container with zero direct SQL (strictly isolated HTTP API client)
    - Full Q12 Accessibility: dynamic scaling, high contrast, keyboard shortcuts
    """
    def __init__(self):
        super().__init__()

        self.title("MediCare Pharmacy Management System — Commercial & TQM Q12 Edition")
        self.geometry("1200x780")
        self.minsize(1050, 680)
        self.configure(fg_color=Theme.BG_APP)

        # Isolated API Client
        self.api_client = APIClient(base_url="http://127.0.0.1:8000")
        self.current_view_key = "dashboard"
        self.current_view_widget = None
        self._monitor_running = True

        # Navigation metadata: (key, icon, label, title, subtitle)
        self.nav_items = [
            ("dashboard", "📊", "Dashboard", "Operational Dashboard", "Clinical KPIs & TQM Quality Safeguards"),
            ("medicines", "💊", "Medicines", "Medicines Formulary", "Master pharmaceutical items and formulations"),
            ("categories", "🗂", "Categories", "Drug Categories", "Therapeutic and clinical class grouping"),
            ("inventory", "📦", "Inventory", "Batch Inventory", "Lot tracking, expiry controls, and physical stock"),
            ("sales", "🧾", "Sales & POS", "Point of Sale & Dispensing", "Prescription fulfillment and counter billing"),
            ("purchases", "🛒", "Purchases", "Inbound Purchases", "Wholesale purchase orders and receiving"),
            ("suppliers", "🏢", "Suppliers", "Wholesale Suppliers", "Pharmaceutical distributor registry"),
            ("customers", "👥", "Customers", "Patient Records", "Patient directory and medication profiles"),
            ("reports", "📈", "Reports", "TQM Reports & Audits", "Quality Pareto metrics and expiration logs"),
            ("settings", "⚙", "Settings", "System Settings", "TQM Q12 Accessibility and interface preferences"),
        ]

        # Subscribe to accessibility updates
        accessibility_manager.subscribe(self._on_accessibility_change)

        self._build_layout()
        self.navigate("dashboard")
        self._start_connection_monitor()

    def _build_layout(self):
        # Master grid: Left Sidebar (col 0, fixed width), Right Content Area (col 1, expands)
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= 1. Fixed Left Sidebar =================
        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=Theme.BG_SIDEBAR,
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Brand header
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=18, pady=(20, 14))

        logo_row = ctk.CTkFrame(brand_frame, fg_color="transparent")
        logo_row.pack(anchor="w")

        ctk.CTkLabel(
            logo_row,
            text="🏥",
            font=ctk.CTkFont(size=22)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_row,
            text="MediCare PMS",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color="#F8FAFC"
        ).pack(side="left")

        ctk.CTkLabel(
            brand_frame,
            text="Clinical SaaS • TQM Q12 Edition",
            font=accessibility_manager.get_font(11),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=(30, 0), pady=(2, 0))

        # Thin divider
        sep = ctk.CTkFrame(self.sidebar, fg_color="#1E293B", height=1)
        sep.pack(fill="x", padx=16, pady=(0, 12))

        # Scrollable Navigation Items Container
        self.nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.nav_scroll.pack(fill="both", expand=True, padx=8, pady=0)

        # Navigation section groupings
        self.nav_buttons = {}

        def _add_section_header(label: str):
            lbl = ctk.CTkLabel(
                self.nav_scroll,
                text=label,
                font=accessibility_manager.get_font(10, weight="bold"),
                text_color="#64748B"
            )
            lbl.pack(anchor="w", padx=12, pady=(10, 4))

        _add_section_header("CORE OPERATIONS")
        for key, icon, label, _, _ in self.nav_items[:4]:
            self._create_nav_button(key, icon, label)

        _add_section_header("TRANSACTIONS & DIRECTORY")
        for key, icon, label, _, _ in self.nav_items[4:8]:
            self._create_nav_button(key, icon, label)

        _add_section_header("QUALITY & PREFERENCES")
        for key, icon, label, _, _ in self.nav_items[8:]:
            self._create_nav_button(key, icon, label)

        # Bottom Sidebar Status Card
        bot_frame = ctk.CTkFrame(self.sidebar, fg_color="#1E293B", corner_radius=10)
        bot_frame.pack(fill="x", padx=14, pady=14)

        self.lbl_sidebar_status = ctk.CTkLabel(
            bot_frame,
            text="⏳ Checking API...",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color="#FBBF24"
        )
        self.lbl_sidebar_status.pack(anchor="w", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            bot_frame,
            text="PostgreSQL 18 • Port 5432",
            font=accessibility_manager.get_font(10),
            text_color="#94A3B8"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # ================= 2. Right Side Content Area =================
        self.right_container = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.right_container.grid(row=0, column=1, sticky="nsew")
        self.right_container.grid_rowconfigure(1, weight=1)
        self.right_container.grid_columnconfigure(0, weight=1)

        # Top Header Bar
        self.top_header = TopHeader(
            self.right_container,
            title="Operational Dashboard",
            subtitle="Clinical KPIs & Quality Safeguards",
            api_client=self.api_client,
            on_toggle_theme=self._on_accessibility_change
        )
        self.top_header.grid(row=0, column=0, sticky="ew")

        # View Area
        self.view_container = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.view_container.grid(row=1, column=0, sticky="nsew")
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

    def _create_nav_button(self, key: str, icon: str, label: str):
        btn = ctk.CTkButton(
            self.nav_scroll,
            text=f"  {icon}  {label}",
            height=38,
            corner_radius=8,
            anchor="w",
            fg_color="transparent",
            text_color="#94A3B8",
            hover_color="#1E293B",
            font=accessibility_manager.get_font(13),
            command=lambda k=key: self.navigate(k)
        )
        btn.pack(fill="x", pady=2, padx=4)
        self.nav_buttons[key] = btn

    def navigate(self, key: str):
        self.current_view_key = key

        # Find metadata for this view
        item_meta = next((item for item in self.nav_items if item[0] == key), None)
        if item_meta:
            _, _, _, title, subtitle = item_meta
            self.top_header.set_title(title, subtitle)

        # Highlight active button
        accent = accessibility_manager.get_accent_color()
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(
                    fg_color=accent,
                    text_color="#FFFFFF" if accent != "#FACC15" else "#000000"
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color="#94A3B8"
                )

        # Cleanly replace view
        if self.current_view_widget:
            self.current_view_widget.destroy()

        if key == "dashboard":
            self.current_view_widget = DashboardView(
                self.view_container,
                self.api_client,
                on_navigate=self.navigate
            )
        elif key == "medicines":
            self.current_view_widget = MedicineView(
                self.view_container,
                self.api_client
            )
        elif key == "categories":
            self.current_view_widget = CategoryView(
                self.view_container,
                self.api_client
            )
        elif key == "inventory":
            self.current_view_widget = InventoryView(
                self.view_container,
                self.api_client
            )
        elif key == "settings":
            self.current_view_widget = SettingsView(
                self.view_container,
                on_theme_change=self._on_accessibility_change
            )
        elif key == "sales":
            self.current_view_widget = ComingSoonView(
                self.view_container,
                "Point of Sale & Dispensing Billing",
                sprint_info="Phase 2 Milestone",
                icon="🧾",
                features=[
                    "Barcode scanner support for rapid medication checkout",
                    "FIFO automatic batch deduction to dispense oldest valid stock first",
                    "Poka-yoke validation blocking sales of expired lots",
                    "Receipt generation with itemized tax and pharmacist signature lines"
                ]
            )
        elif key == "purchases":
            self.current_view_widget = ComingSoonView(
                self.view_container,
                "Wholesale Purchases & Inbound POs",
                sprint_info="Phase 2 Milestone",
                icon="🛒",
                features=[
                    "Purchase order generation with automated reorder level triggers",
                    "Multi-batch receiving dock with manufacturer expiry verification",
                    "Supplier invoice reconciliation and payment terms tracking",
                    "TQM receiving inspection audit trail"
                ]
            )
        elif key == "suppliers":
            self.current_view_widget = ComingSoonView(
                self.view_container,
                "Pharmaceutical Suppliers Directory",
                sprint_info="Phase 2 Milestone",
                icon="🏢",
                features=[
                    "Drug manufacturing and wholesale distributor licenses",
                    "Primary contact, address, and GST registration records",
                    "Supplier performance rating and on-time delivery audits",
                    "Linked purchase history and outstanding balances"
                ]
            )
        elif key == "customers":
            self.current_view_widget = ComingSoonView(
                self.view_container,
                "Patient & Customer Records",
                sprint_info="Phase 2 Milestone",
                icon="👥",
                features=[
                    "Patient demographics, contact details, and chronic condition notes",
                    "Prescription history and dispensing log lookup",
                    "Drug allergy warnings and contraindication alerts",
                    "Loyalty credit and account balance management"
                ]
            )
        elif key == "reports":
            self.current_view_widget = ComingSoonView(
                self.view_container,
                "TQM Quality & Pareto Analytics",
                sprint_info="Phase 2 Milestone",
                icon="📈",
                features=[
                    "Pareto 80/20 analysis on fast-moving vs stagnant pharmaceutical stock",
                    "Batch expiration hazard curve and quarantine defect audits",
                    "Daily sales volume and profit margin reconciliations",
                    "Exportable compliance reports for regulatory drug inspections"
                ]
            )

        self.current_view_widget.grid(row=0, column=0, sticky="nsew")

    def _start_connection_monitor(self):
        def _loop():
            while self._monitor_running:
                try:
                    health = self.api_client.get_health()
                    self.after(0, self._render_health, health)
                except Exception:
                    self.after(0, self._render_health, {})
                time.sleep(10)

        threading.Thread(target=_loop, daemon=True).start()

    def _render_health(self, health: dict):
        api_ok = health.get("api_service") == "running"
        db_ok = health.get("database", {}).get("database_connected", False)

        # Update TopHeader
        self.top_header.update_health_status(api_ok, db_ok)

        # Update Sidebar
        if api_ok and db_ok:
            self.lbl_sidebar_status.configure(text="● API & DB Online", text_color="#34D399")
        elif api_ok and not db_ok:
            self.lbl_sidebar_status.configure(text="● DB Degraded", text_color="#F87171")
        else:
            self.lbl_sidebar_status.configure(text="● Backend Offline", text_color="#EF4444")

    def _on_accessibility_change(self):
        self.configure(fg_color=Theme.BG_APP)
        # Re-render active view to apply font scaling or contrast changes
        self.navigate(self.current_view_key)

    def destroy(self):
        self._monitor_running = False
        super().destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
