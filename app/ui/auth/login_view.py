import customtkinter as ctk
from typing import Callable, Dict, Any, Optional
from app.ui.theme import Theme
from app.ui.accessibility import accessibility_manager
from app.client.api_client import APIClient


class LoginView(ctk.CTkFrame):
    """
    Multi-Stakeholder Authentication View.
    Supports secure login, 1-click demo role switching for all 7 stakeholders,
    and patient self-registration.
    """
    def __init__(self, parent, api_client: APIClient, on_login_success: Callable[[Dict[str, Any]], None]):
        super().__init__(parent, fg_color=Theme.BG_APP)
        self.api_client = api_client
        self.on_login_success = on_login_success

        self._build_ui()

    def _build_ui(self):
        # Center container
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            self,
            fg_color=Theme.BG_CARD,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER,
            width=540
        )
        card.grid(row=0, column=0, padx=20, pady=20)

        # Header branding
        badge = ctk.CTkFrame(card, fg_color=Theme.PRIMARY, width=48, height=48, corner_radius=12)
        badge.pack(pady=(28, 10))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text="🏥", font=accessibility_manager.get_font(24)).pack(expand=True)

        ctk.CTkLabel(
            card,
            text="MediCare PMS — Multi-Stakeholder SaaS",
            font=accessibility_manager.get_font(18, weight="bold"),
            text_color=Theme.TEXT_MAIN
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            card,
            text="Select stakeholder role or sign in with your credentials",
            font=accessibility_manager.get_font(12),
            text_color=Theme.TEXT_MUTED
        ).pack(pady=(0, 20))

        # Credentials Form
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.pack(fill="x", padx=40)

        ctk.CTkLabel(form_frame, text="Username / Email", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", pady=(0, 4))
        self.txt_username = ctk.CTkEntry(form_frame, placeholder_text="Enter username...", height=38, font=accessibility_manager.get_font(13))
        self.txt_username.pack(fill="x", pady=(0, 14))

        ctk.CTkLabel(form_frame, text="Password", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", pady=(0, 4))
        self.txt_password = ctk.CTkEntry(form_frame, placeholder_text="Enter password...", show="●", height=38, font=accessibility_manager.get_font(13))
        self.txt_password.pack(fill="x", pady=(0, 10))
        self.txt_password.bind("<Return>", lambda e: self._handle_login())

        self.lbl_error = ctk.CTkLabel(form_frame, text="", font=accessibility_manager.get_font(12, weight="bold"), text_color=Theme.DANGER_TEXT)
        self.lbl_error.pack(anchor="w", pady=(0, 10))

        btn_login = ctk.CTkButton(
            form_frame,
            text="Sign In to Portal →",
            height=42,
            font=accessibility_manager.get_font(14, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            cursor="hand2",
            command=self._handle_login
        )
        btn_login.pack(fill="x", pady=(0, 16))

        # Divider
        div = ctk.CTkFrame(card, height=1, fg_color=Theme.BORDER)
        div.pack(fill="x", padx=40, pady=10)

        # Quick-Switch Stakeholder Demo Bar
        ctk.CTkLabel(
            card,
            text="⚡ QUICK-SWITCH STAKEHOLDER DEMO (1-CLICK SIGN IN)",
            font=accessibility_manager.get_font(10, weight="bold"),
            text_color=Theme.TEXT_MUTED
        ).pack(pady=(4, 8))

        pills_frame = ctk.CTkFrame(card, fg_color="transparent")
        pills_frame.pack(fill="x", padx=20, pady=(0, 20))

        stakeholder_demos = [
            ("👑 Super Admin", "superadmin", "super123"),
            ("🏢 Owner", "owner", "owner123"),
            ("💊 Pharmacist", "pharmacist", "pharma123"),
            ("🧾 Cashier", "cashier", "cashier123"),
            ("📦 Inventory", "inventory", "stock123"),
            ("🚚 Supplier", "supplier", "vendor123"),
            ("👤 Patient", "customer", "patient123"),
        ]

        row1 = ctk.CTkFrame(pills_frame, fg_color="transparent")
        row1.pack(pady=3)
        row2 = ctk.CTkFrame(pills_frame, fg_color="transparent")
        row2.pack(pady=3)

        for i, (title, u, p) in enumerate(stakeholder_demos):
            parent_row = row1 if i < 4 else row2
            btn = ctk.CTkButton(
                parent_row,
                text=title,
                width=115,
                height=30,
                font=accessibility_manager.get_font(11, weight="bold"),
                fg_color=Theme.BG_MUTED,
                hover_color=Theme.SECONDARY_HOVER,
                text_color=Theme.TEXT_MAIN,
                border_width=1,
                border_color=Theme.BORDER,
                cursor="hand2",
                command=lambda user=u, pwd=p: self._fill_and_login(user, pwd)
            )
            btn.pack(side="left", padx=4)

        # Footer links: Patient self-registration
        footer_frame = ctk.CTkFrame(card, fg_color="transparent")
        footer_frame.pack(pady=(0, 16))
        ctk.CTkButton(
            footer_frame,
            text="New Patient? Self-Register Here",
            fg_color="transparent",
            text_color=Theme.PRIMARY,
            hover=False,
            font=accessibility_manager.get_font(12, weight="bold"),
            cursor="hand2",
            command=self._open_patient_registration
        ).pack()

    def _fill_and_login(self, username: str, password: str):
        self.txt_username.delete(0, "end")
        self.txt_username.insert(0, username)
        self.txt_password.delete(0, "end")
        self.txt_password.insert(0, password)
        self._handle_login()

    def _handle_login(self):
        username = self.txt_username.get().strip()
        password = self.txt_password.get().strip()

        if not username or not password:
            self.lbl_error.configure(text="Please enter both username and password.")
            return

        try:
            user_data = self.api_client.login(username, password)
            self.lbl_error.configure(text="")
            self.on_login_success(user_data)
        except Exception as e:
            err_msg = str(e)
            if "401" in err_msg or "Invalid" in err_msg:
                self.lbl_error.configure(text="Invalid username or password.")
            elif "deactivated" in err_msg.lower() or "inactive" in err_msg.lower():
                self.lbl_error.configure(text="Account or pharmacy is suspended.")
            else:
                self.lbl_error.configure(text=f"Authentication error: {err_msg[:45]}")

    def _open_patient_registration(self):
        RegisterPatientModal(self.winfo_toplevel(), self.api_client, on_registered=self._fill_and_login)


class RegisterPatientModal(ctk.CTkToplevel):
    def __init__(self, parent, api_client: APIClient, on_registered: Callable[[str, str], None]):
        super().__init__(parent)
        self.api_client = api_client
        self.on_registered = on_registered

        self.title("Patient Self-Registration")
        self.geometry("460x520")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_APP)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        container = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(container, text="👤 Patient Registration", font=accessibility_manager.get_font(16, weight="bold"), text_color=Theme.TEXT_MAIN).pack(pady=(16, 12))

        self.txt_name = self._make_field(container, "Full Name *", "Patient full name")
        self.txt_phone = self._make_field(container, "Phone Number *", "+91 98765 43210")
        self.txt_email = self._make_field(container, "Email Address *", "patient@email.com")
        self.txt_address = self._make_field(container, "Residential Address", "Street and city")
        self.txt_pwd = self._make_field(container, "Password *", "Choose secure password", show="●")

        self.lbl_err = ctk.CTkLabel(container, text="", font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.DANGER_TEXT)
        self.lbl_err.pack(pady=4)

        btn_reg = ctk.CTkButton(
            container,
            text="Complete Patient Registration",
            height=38,
            font=accessibility_manager.get_font(13, weight="bold"),
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            command=self._submit
        )
        btn_reg.pack(fill="x", padx=30, pady=(8, 16))

    def _make_field(self, parent, label: str, placeholder: str, show: Optional[str] = None):
        ctk.CTkLabel(parent, text=label, font=accessibility_manager.get_font(11, weight="bold"), text_color=Theme.TEXT_MAIN).pack(anchor="w", padx=30, pady=(4, 2))
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=32, show=show, font=accessibility_manager.get_font(12))
        entry.pack(fill="x", padx=30, pady=(0, 4))
        return entry

    def _submit(self):
        name = self.txt_name.get().strip()
        phone = self.txt_phone.get().strip()
        email = self.txt_email.get().strip()
        address = self.txt_address.get().strip()
        password = self.txt_pwd.get().strip()

        if not name or not phone or not email or not password:
            self.lbl_err.configure(text="Please complete all required fields.")
            return

        try:
            res = self.api_client.register_patient_account({
                "name": name,
                "phone": phone,
                "email": email,
                "address": address,
                "password": password
            })
            self.destroy()
            self.on_registered(email, password)
        except Exception as e:
            self.lbl_err.configure(text=str(e)[:45])
