"""
MediCare Pharmacy Management System — Commercial Desktop Main Window.
Implements:
- Responsive desktop layout with collapsible left sidebar (240px <-> 68px)
- Pinned TopHeader bar with title, breadcrumbs, search, notification alerts bell, and theme switch
- Real-time connection monitoring with PostgreSQL 18
- Complete accessibility controls with global hotkeys (Ctrl+1..Ctrl+0, Ctrl+B, Ctrl+F, Esc)
- 11 domain modules with honest, transparent milestone indicators
"""
import threading
import time
from typing import Dict, Any, List, Optional
import customtkinter as ctk

from app.client.api_client import APIClient
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import accessibility_manager
from app.ui.common.async_task import init_async, run_in_background, _gui_queue
from app.ui.components.header import TopHeader
from app.ui.dashboard.dashboard_view import DashboardView
from app.ui.categories.category_view import CategoryView
from app.ui.medicines.medicine_view import MedicineView
from app.ui.inventory.inventory_view import InventoryView
from app.ui.billing.billing_view import BillingView
from app.ui.settings.settings_view import SettingsView
from app.ui.common.roadmap_view import RoadmapView


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MediCare Pharmacy Management System — Commercial & TQM Q12 Edition")
        self.geometry("1240x800")
        self.minsize(1020, 660)
        self.configure(fg_color=Theme.BG_APP)

        # Isolated API Client
        self.api_client = APIClient(base_url="http://127.0.0.1:8000")
        self.current_view_key = "dashboard"
        self.current_view_widget = None
        self._monitor_running = True
        self.is_sidebar_collapsed = False

        # Navigation specification: (key, icon, label, title, subtitle)
        self.nav_items = [
            ("dashboard", "📊", "Dashboard", "Operational Dashboard", "Clinical KPIs & TQM Quality Safeguards"),
            ("medicines", "💊", "Medicines", "Medicines Formulary", "Master pharmaceutical items and formulations"),
            ("categories", "🗂", "Categories", "Drug Categories", "Therapeutic and clinical class grouping"),
            ("inventory", "📦", "Inventory", "Batch Inventory", "Lot tracking, expiry controls, and physical stock"),
            ("sales", "🧾", "Sales & Billing", "Point of Sale & Dispensing", "Prescription fulfillment and counter billing"),
            ("purchases", "🛒", "Purchases", "Inbound Purchases", "Wholesale purchase orders and receiving"),
            ("suppliers", "🏢", "Suppliers", "Wholesale Suppliers", "Pharmaceutical distributor registry"),
            ("customers", "👥", "Customers", "Patient Records", "Patient directory and medication profiles"),
            ("reports", "📈", "Reports & TQM", "TQM Quality Reports", "Quality Pareto metrics and expiration logs"),
            ("users", "👤", "Users & Roles", "Users & Permissions", "Role-Based Access Control (RBAC) & Audit Log"),
            ("settings", "⚙", "Settings", "System Settings", "TQM Q12 Accessibility and interface preferences"),
        ]

        # Subscribe to accessibility updates
        accessibility_manager.subscribe(self._on_accessibility_change)

        # Initialize thread-safe async queue pump
        init_async(self)

        self._build_layout()
        self._bind_keyboard_shortcuts()
        self.navigate("dashboard")
        self._start_connection_monitor()

    def _build_layout(self):
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ================= 1. Left Sidebar Navigation =================
        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=Theme.BG_SIDEBAR,
            border_width=1,
            border_color=Theme.BORDER
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.pack_propagate(False)

        # Brand Container
        self.brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.brand_frame.pack(fill="x", padx=14, pady=(16, 10))

        self.logo_row = ctk.CTkFrame(self.brand_frame, fg_color="transparent")
        self.logo_row.pack(anchor="w")

        # Teal logo badge
        self.logo_badge = ctk.CTkFrame(self.logo_row, fg_color=Theme.PRIMARY, width=36, height=36, corner_radius=8)
        self.logo_badge.pack(side="left", padx=(0, 10))
        self.logo_badge.pack_propagate(False)

        self.lbl_logo_icon = ctk.CTkLabel(
            self.logo_badge,
            text="🏥",
            font=accessibility_manager.get_font(18)
        )
        self.lbl_logo_icon.pack(expand=True)

        self.logo_titles = ctk.CTkFrame(self.logo_row, fg_color="transparent")
        self.logo_titles.pack(side="left")

        self.lbl_logo_text = ctk.CTkLabel(
            self.logo_titles,
            text="MediCare PMS",
            font=accessibility_manager.get_font(16, weight="bold"),
            text_color=Theme.TEXT_MAIN
        )
        self.lbl_logo_text.pack(anchor="w")

        self.lbl_logo_sub = ctk.CTkLabel(
            self.logo_titles,
            text="Clinical SaaS • TQM Q12",
            font=accessibility_manager.get_font(10),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_logo_sub.pack(anchor="w")

        self.brand_sep = ctk.CTkFrame(self.sidebar, fg_color=Theme.BORDER, height=1)
        self.brand_sep.pack(fill="x", padx=14, pady=(8, 10))

        # Bottom Sidebar Connection Pill packed first at bottom so it never clips
        self.bot_frame = ctk.CTkFrame(self.sidebar, fg_color=Theme.BG_MUTED, corner_radius=10)
        self.bot_frame.pack(side="bottom", fill="x", padx=12, pady=12)

        self.lbl_sidebar_status = ctk.CTkLabel(
            self.bot_frame,
            text="⏳ Checking API...",
            font=accessibility_manager.get_font(11, weight="bold"),
            text_color=Theme.SUCCESS_TEXT
        )
        self.lbl_sidebar_status.pack(anchor="w", padx=10, pady=(6, 1))

        self.lbl_sidebar_db = ctk.CTkLabel(
            self.bot_frame,
            text="PostgreSQL 18 • Port 5432",
            font=accessibility_manager.get_font(10),
            text_color=Theme.TEXT_MUTED
        )
        self.lbl_sidebar_db.pack(anchor="w", padx=10, pady=(0, 6))

        # Scrollable Nav Buttons in the middle
        self.nav_scroll = ctk.CTkScrollableFrame(self.sidebar, fg_color="transparent")
        self.nav_scroll.pack(side="top", fill="both", expand=True, padx=6, pady=0)
        self.nav_scroll.grid_columnconfigure(0, weight=1)

        self.nav_buttons = {}
        self.section_headers = []
        self._nav_row_counter = 0

        def _add_section(label: str):
            hdr = ctk.CTkLabel(
                self.nav_scroll,
                text=label,
                font=accessibility_manager.get_font(9, weight="bold"),
                text_color=Theme.TEXT_MUTED
            )
            hdr.grid(row=self._nav_row_counter, column=0, sticky="w", padx=12, pady=(10, 3))
            self.section_headers.append(hdr)
            self._nav_row_counter += 1

        def _create_nav_button(key: str, icon: str, label: str):
            btn = ctk.CTkButton(
                self.nav_scroll,
                text=f"  {icon}   {label}",
                height=38,
                corner_radius=10,
                anchor="w",
                fg_color="transparent",
                text_color=Theme.TEXT_MUTED,
                hover_color=Theme.SECONDARY_HOVER,
                font=accessibility_manager.get_font(12),
                command=lambda k=key: self.navigate(k)
            )
            btn.grid(row=self._nav_row_counter, column=0, sticky="ew", pady=2, padx=4)
            self.nav_buttons[key] = btn
            self._nav_row_counter += 1

        _add_section("OPERATIONS")
        for key, icon, label, _, _ in self.nav_items[:4]:
            _create_nav_button(key, icon, label)

        _add_section("TRANSACTIONS & DIRECTORY")
        for key, icon, label, _, _ in self.nav_items[4:8]:
            _create_nav_button(key, icon, label)

        _add_section("QUALITY & SYSTEM")
        for key, icon, label, _, _ in self.nav_items[8:]:
            _create_nav_button(key, icon, label)

        # ================= 2. Main Right Container =================
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
            on_toggle_theme=self._on_accessibility_change,
            on_toggle_sidebar=self.toggle_sidebar,
            on_search=self._handle_global_search
        )
        self.top_header.grid(row=0, column=0, sticky="ew")

        # View Area
        self.view_container = ctk.CTkFrame(self.right_container, fg_color="transparent")
        self.view_container.grid(row=1, column=0, sticky="nsew")
        self.view_container.grid_rowconfigure(0, weight=1)
        self.view_container.grid_columnconfigure(0, weight=1)

    def toggle_sidebar(self):
        self.is_sidebar_collapsed = not self.is_sidebar_collapsed
        new_width = 68 if self.is_sidebar_collapsed else 240
        self.grid_columnconfigure(0, weight=0, minsize=new_width)
        self.sidebar.configure(width=new_width)

        if self.is_sidebar_collapsed:
            # 1. Collapse logo header to icon badge only, centered
            self.logo_titles.pack_forget()
            self.logo_badge.pack_configure(padx=0)
            self.logo_row.pack_configure(anchor="center")
            self.brand_frame.pack_configure(padx=4)

            # 2. Hide section headers cleanly (retaining grid positions)
            for hdr in self.section_headers:
                hdr.grid_remove()

            # 3. Collapse nav buttons to icon-only centered with prominent icon font
            for key, btn in self.nav_buttons.items():
                icon = next(item[1] for item in self.nav_items if item[0] == key)
                btn.configure(text=icon, anchor="center", font=accessibility_manager.get_font(15))
                btn.grid_configure(padx=2)

            # 4. Collapse bottom status pill to compact dot
            self.bot_frame.pack_configure(padx=6, pady=8)
            self.lbl_sidebar_db.pack_forget()
            self.lbl_sidebar_status.pack_configure(anchor="center", padx=0, pady=6)
            self.lbl_sidebar_status.configure(text="●", font=accessibility_manager.get_font(16))
        else:
            # 1. Expand logo header
            self.brand_frame.pack_configure(padx=14)
            self.logo_row.pack_configure(anchor="w")
            self.logo_badge.pack_configure(padx=(0, 10))
            self.logo_titles.pack(side="left")

            # 2. Restore all section headers in their exact original spots
            for hdr in self.section_headers:
                hdr.grid()

            # 3. Expand nav buttons to full icon + label
            for key, btn in self.nav_buttons.items():
                meta = next(item for item in self.nav_items if item[0] == key)
                btn.configure(text=f"  {meta[1]}   {meta[2]}", anchor="w", font=accessibility_manager.get_font(12))
                btn.grid_configure(padx=4)

            # 4. Expand bottom status pill to full text
            self.bot_frame.pack_configure(padx=12, pady=12)
            self.lbl_sidebar_status.pack_configure(anchor="w", padx=10, pady=(6, 1))
            self.lbl_sidebar_status.configure(font=accessibility_manager.get_font(11, weight="bold"))
            self.lbl_sidebar_db.pack(anchor="w", padx=10, pady=(0, 6))
            self._update_sidebar_health_display()

        # 5. Visual update on top header hamburger button
        if hasattr(self.top_header, "update_sidebar_button"):
            self.top_header.update_sidebar_button(self.is_sidebar_collapsed)

    def _bind_keyboard_shortcuts(self):
        # Universal dispatcher that handles all Ctrl keys, NumLock/CapsLock state, F-keys, and arrows
        self.bind_all("<Key>", self._on_global_key_press)

        # Redundant explicit bindings across root and all widgets for maximum responsiveness
        for pattern in [
            "<Control-b>", "<Control-B>", "<Control-Key-b>", "<Control-Key-B>",
        ]:
            self.bind_all(pattern, lambda e: (self.toggle_sidebar(), "break")[1])

        for pattern in ["<Control-f>", "<Control-F>", "<Control-Key-f>", "<Control-Key-F>"]:
            self.bind_all(pattern, lambda e: (self.focus_search(), "break")[1])

        for pattern in ["<Control-r>", "<Control-R>", "<Control-Key-r>", "<Control-Key-R>", "<F5>"]:
            self.bind_all(pattern, lambda e: (self.refresh_active_view(), "break")[1])

        for pattern in ["<Control-n>", "<Control-N>", "<Control-Key-n>", "<Control-Key-N>"]:
            self.bind_all(pattern, lambda e: (self.trigger_new_record(), "break")[1])

        for pattern in ["<F1>", "<Control-h>", "<Control-H>", "<Control-Key-h>", "<Control-Key-H>"]:
            self.bind_all(pattern, lambda e: (self.show_shortcuts_modal(), "break")[1])

        for pattern in ["<Control-u>", "<Control-U>", "<Control-Key-u>", "<Control-Key-U>"]:
            self.bind_all(pattern, lambda e: (self.navigate("users"), "break")[1])

        self.bind_all("<Escape>", lambda e: (self._handle_escape(), "break")[1])

        # Page jump hotkeys (Ctrl+1 .. Ctrl+0)
        nav_map = {
            "1": "dashboard",
            "2": "medicines",
            "3": "categories",
            "4": "inventory",
            "5": "sales",
            "6": "purchases",
            "7": "suppliers",
            "8": "customers",
            "9": "reports",
            "0": "settings",
        }
        for num, view_key in nav_map.items():
            for pat in [f"<Control-Key-{num}>", f"<Control-{num}>", f"<Control-KP_{num}>"]:
                self.bind_all(pat, lambda e, vk=view_key: (self.navigate(vk), "break")[1])

    def _is_entry_focused(self) -> bool:
        try:
            focused = self.focus_get()
            if not focused:
                return False
            cls = focused.winfo_class().lower()
            return "entry" in cls or "text" in cls
        except Exception:
            return False

    def _on_global_key_press(self, event):
        keysym = event.keysym
        is_ctrl = bool(event.state & 4)
        is_entry = self._is_entry_focused()

        # Handle global hotkeys that ignore text focus:
        if is_ctrl:
            k = keysym.lower()
            if k == 'b':
                self.toggle_sidebar()
                return "break"
            elif k == 'f':
                self.focus_search()
                return "break"
            elif k == 'r':
                self.refresh_active_view()
                return "break"
            elif k == 'n':
                self.trigger_new_record()
                return "break"
            elif k == 'h':
                self.show_shortcuts_modal()
                return "break"
            elif k == 'u':
                self.navigate("users")
                return "break"
            elif k in "1234567890":
                mapping = {
                    "1": "dashboard",
                    "2": "medicines",
                    "3": "categories",
                    "4": "inventory",
                    "5": "sales",
                    "6": "purchases",
                    "7": "suppliers",
                    "8": "customers",
                    "9": "reports",
                    "0": "settings",
                }
                if k in mapping:
                    self.navigate(mapping[k])
                    return "break"

        # Keypad numbers with Ctrl
        if is_ctrl and keysym.startswith("KP_"):
            kp_digit = keysym.replace("KP_", "")
            mapping = {
                "1": "dashboard",
                "2": "medicines",
                "3": "categories",
                "4": "inventory",
                "5": "sales",
                "6": "purchases",
                "7": "suppliers",
                "8": "customers",
                "9": "reports",
                "0": "settings",
            }
            if kp_digit in mapping:
                self.navigate(mapping[kp_digit])
                return "break"

        if keysym == "F1":
            self.show_shortcuts_modal()
            return "break"
        elif keysym == "F5":
            self.refresh_active_view()
            return "break"
        elif keysym == "Escape":
            self._handle_escape()
            return "break"
        elif keysym == "Up" and not is_entry:
            self._navigate_sidebar_arrow(-1)
            return "break"
        elif keysym == "Down" and not is_entry:
            self._navigate_sidebar_arrow(1)
            return "break"

    def focus_search(self):
        if hasattr(self, "top_header") and hasattr(self.top_header, "search_entry"):
            self.top_header.search_entry.focus_set()
            try:
                self.top_header.search_entry.select_range(0, "end")
            except Exception:
                pass

    def refresh_active_view(self):
        if not self.current_view_widget:
            return
        if hasattr(self.current_view_widget, "_load_data"):
            self.current_view_widget._load_data()
        elif hasattr(self.current_view_widget, "load_batches"):
            self.current_view_widget.load_batches()
        elif hasattr(self.current_view_widget, "_fetch_data"):
            self.current_view_widget._fetch_data()
        elif hasattr(self.current_view_widget, "_load_dashboard"):
            self.current_view_widget._load_dashboard()

    def trigger_new_record(self):
        if not self.current_view_widget:
            return
        if hasattr(self.current_view_widget, "_open_add_modal"):
            self.current_view_widget._open_add_modal()
        elif hasattr(self.current_view_widget, "_open_receive_modal"):
            self.current_view_widget._open_receive_modal()
        elif hasattr(self.current_view_widget, "_open_new_bill_modal"):
            self.current_view_widget._open_new_bill_modal()
        elif self.current_view_key == "dashboard":
            self.navigate("medicines")
            if hasattr(self.current_view_widget, "_open_add_modal"):
                self.current_view_widget._open_add_modal()

    def show_shortcuts_modal(self):
        from app.ui.components.dialogs import ShortcutsModal
        ShortcutsModal(self)

    def _handle_escape(self):
        try:
            focused = self.focus_get()
            if focused:
                self.focus_set()
        except Exception:
            pass

    def _navigate_sidebar_arrow(self, direction: int):
        keys = [item[0] for item in self.nav_items]
        try:
            curr_idx = keys.index(self.current_view_key)
        except ValueError:
            curr_idx = 0
        new_idx = (curr_idx + direction) % len(keys)
        self.navigate(keys[new_idx])

    def _handle_global_search(self, query: str):
        self.navigate("medicines")
        if hasattr(self.current_view_widget, "search_entry"):
            self.current_view_widget.search_entry.delete(0, "end")
            self.current_view_widget.search_entry.insert(0, query)
            self.current_view_widget._apply_filters()

    def navigate(self, key: str):
        self.current_view_key = key

        # Update TopHeader Title and Subtitle
        item_meta = next((item for item in self.nav_items if item[0] == key), None)
        if item_meta:
            _, _, _, title, subtitle = item_meta
            self.top_header.set_title(title, subtitle)

        # Highlight active sidebar button
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
                    text_color=Theme.TEXT_MUTED
                )

        # Destroy old view
        if self.current_view_widget:
            self.current_view_widget.destroy()

        # Instantiate new view
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
            self.current_view_widget = BillingView(
                self.view_container,
                self.api_client
            )
        elif key == "purchases":
            self.current_view_widget = RoadmapView(
                self.view_container,
                module_name="Purchases & Inbound Invoices",
                icon="🛒",
                milestone="Phase 2 Sprint — Procurement Pipeline",
                overview="Manages procurement purchase orders (POs), vendor invoice reconciliations, and receiving dock audits.",
                schema_info=[
                    {"table": "purchase_orders", "desc": "Order number, supplier ID, expected date, status, total cost"},
                    {"table": "po_items", "desc": "Ordered medicine ID, quantity requested, contracted unit cost"}
                ],
                planned_endpoints=[
                    "POST /api/v1/purchases/orders (Create PO)",
                    "PUT /api/v1/purchases/receive (Receive & create batch lots)",
                    "GET /api/v1/purchases/pending (Pending deliveries)"
                ],
                tqm_safeguards=[
                    "Receiving dock inspection: Expiry date validation before lot creation",
                    "Non-negative quantity check constraints enforced on line items",
                    "Vendor fulfillment lead-time audit logging"
                ]
            )
        elif key == "suppliers":
            self.current_view_widget = RoadmapView(
                self.view_container,
                module_name="Wholesale Pharmaceutical Suppliers",
                icon="🏢",
                milestone="Database Table Ready — Service Integration Pending",
                overview="Maintains licensed pharmaceutical distributors, contact persons, tax IDs, and delivery SLAs.",
                schema_info=[
                    {"table": "suppliers", "desc": "ID, name, contact person, phone, email, address, is_active (Table exists in PostgreSQL 18)"}
                ],
                planned_endpoints=[
                    "GET /api/v1/suppliers (List active vendors)",
                    "POST /api/v1/suppliers (Register new distributor)",
                    "PUT /api/v1/suppliers/{id} (Update vendor profile)"
                ],
                tqm_safeguards=[
                    "Unique name constraint on supplier table",
                    "Foreign key cascade restrictions preserve purchase order history",
                    "Supplier performance rating tracking"
                ]
            )
        elif key == "customers":
            self.current_view_widget = RoadmapView(
                self.view_container,
                module_name="Patient & Customer Directory",
                icon="👥",
                milestone="Phase 2 Sprint — Patient Registry",
                overview="Stores patient demographics, prescription histories, medication allergy alerts, and account balances.",
                schema_info=[
                    {"table": "customers", "desc": "Patient name, phone, email, chronic conditions, loyalty credits"},
                    {"table": "prescriptions", "desc": "Doctor name, clinic license, diagnosis, validity date"}
                ],
                planned_endpoints=[
                    "GET /api/v1/customers/search?phone=... (Rapid lookup)",
                    "POST /api/v1/customers (Enroll patient)",
                    "GET /api/v1/customers/{id}/history (Medication profile)"
                ],
                tqm_safeguards=[
                    "Drug allergy contraindication popups during checkout",
                    "Prescription expiry validation before dispensing controlled drugs",
                    "HIPAA-compliant personal health information audit logs"
                ]
            )
        elif key == "reports":
            self.current_view_widget = RoadmapView(
                self.view_container,
                module_name="TQM Quality & Audit Reports",
                icon="📈",
                milestone="Phase 2 Sprint — Quality Analytics",
                overview="Generates Pareto 80/20 analysis charts, expiration hazard curves, and stock turnover metrics.",
                schema_info=[
                    {"table": "audit_logs", "desc": "User ID, action type, table affected, before/after delta snapshot"}
                ],
                planned_endpoints=[
                    "GET /api/v1/reports/pareto (Fast vs slow moving stock)",
                    "GET /api/v1/reports/expiry-hazard (Hazard rate analysis)",
                    "GET /api/v1/reports/compliance-audit (Exportable regulatory PDF)"
                ],
                tqm_safeguards=[
                    "Pareto 80/20 inventory classification to eliminate stockouts",
                    "Defect tracking: Quarantine logs for damaged or expired shipments",
                    "Zero manual tampering: Reports generated directly from immutable DB rows"
                ]
            )
        elif key == "users":
            self.current_view_widget = RoadmapView(
                self.view_container,
                module_name="User Accounts & Role-Based Permissions (RBAC)",
                icon="👤",
                milestone="Phase 2 Sprint — Authentication Service",
                overview="Governs system access across Admin, Pharmacist, and Cashier roles with bcrypt password hashing and JWT sessions.",
                schema_info=[
                    {"table": "users", "desc": "Username, hashed_password, role, is_active, last_login"},
                    {"table": "roles_permissions", "desc": "Role definitions and granular capability matrix"}
                ],
                planned_endpoints=[
                    "POST /api/v1/auth/login (JWT token issuance)",
                    "POST /api/v1/users (Admin user creation)",
                    "GET /api/v1/auth/me (Active session permissions)"
                ],
                tqm_safeguards=[
                    "Bcrypt password hashing with salt (passlib/bcrypt installed)",
                    "Least-privilege principle: Cashiers blocked from modifying formulary",
                    "Failed login lockout to prevent brute-force attacks"
                ]
            )

        self.current_view_widget.grid(row=0, column=0, sticky="nsew")

    def _start_connection_monitor(self):
        def _loop():
            while self._monitor_running:
                try:
                    health = self.api_client.get_health()
                    try:
                        metrics = self.api_client.get_dashboard_metrics()
                        low_stock = metrics.get("low_stock_medicines", 0)
                        exp_soon = metrics.get("expiring_soon_batches", 0)
                        alerts_list = []
                        if low_stock > 0:
                            alerts_list.append({
                                "title": "Low Stock Notice",
                                "badge": "REORDER",
                                "variant": "danger",
                                "message": f"{low_stock} pharmaceutical items have fallen below minimum reorder thresholds."
                            })
                        if exp_soon > 0:
                            alerts_list.append({
                                "title": "Near Expiry Batches",
                                "badge": "EXPIRING",
                                "variant": "warning",
                                "message": f"{exp_soon} batches will expire within the next 30 days."
                            })
                    except Exception:
                        alerts_list = []

                    if not self._monitor_running:
                        break
                    _gui_queue.put((self._render_health, (health, alerts_list), {}))
                except Exception:
                    if not self._monitor_running:
                        break
                    _gui_queue.put((self._render_health, ({}, []), {}))
                time.sleep(10)

        threading.Thread(target=_loop, daemon=True).start()

    def _render_health(self, health: dict, alerts: list):
        self._last_api_ok = health.get("api_service") == "running"
        self._last_db_ok = health.get("database", {}).get("database_connected", False)

        # Update TopHeader
        self.top_header.update_health_status(self._last_api_ok, self._last_db_ok)
        self.top_header.set_alerts(alerts)

        # Update Sidebar
        self._update_sidebar_health_display()

    def _update_sidebar_health_display(self):
        api_ok = getattr(self, "_last_api_ok", False)
        db_ok = getattr(self, "_last_db_ok", False)
        if not self.is_sidebar_collapsed:
            if api_ok and db_ok:
                self.lbl_sidebar_status.configure(text="● API & DB Online", text_color="#34D399")
            elif api_ok and not db_ok:
                self.lbl_sidebar_status.configure(text="● DB Degraded", text_color="#F87171")
            else:
                self.lbl_sidebar_status.configure(text="● Backend Offline", text_color="#EF4444")
        else:
            dot_color = "#34D399" if (api_ok and db_ok) else ("#F87171" if api_ok else "#EF4444")
            self.lbl_sidebar_status.configure(text="●", text_color=dot_color)

    def _on_accessibility_change(self, event="theme"):
        self.configure(fg_color=Theme.BG_APP)
        if event == "theme":
            self.navigate(self.current_view_key)
        else:
            self.update_idletasks()

    def destroy(self):
        self._monitor_running = False
        super().destroy()


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
