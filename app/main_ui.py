import threading
import customtkinter as ctk
from app.client.api_client import APIClient

class PharmacyManagementApp(ctk.CTk):
    """
    Desktop UI Entry Point for Pharmacy Management System.
    Emphasizes Q12 Accessibility: Minimalist UI, Dark Mode, High Contrast & Clear Indicators.
    """
    def __init__(self):
        super().__init__()
        
        # Configure Q12 Accessibility Baseline
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.title("Pharmacy Management System — Integration Check")
        self.geometry("720x520")
        self.minsize(600, 450)
        
        # Instantiate decoupled API client
        self.api_client = APIClient(base_url="http://127.0.0.1:8000")
        
        self._build_ui()
        self.trigger_health_check()

    def _build_ui(self):
        # Header Container
        self.header_frame = ctk.CTkFrame(self, corner_radius=10)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="🏥 Pharmacy Management System",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.title_label.pack(pady=(15, 5))
        
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="TQM Error Prevention & Q12 Accessibility Standards",
            font=ctk.CTkFont(size=14, slant="italic"),
            text_color="#9CA3AF"
        )
        self.subtitle_label.pack(pady=(0, 15))

        # Status Card
        self.status_card = ctk.CTkFrame(self, corner_radius=10)
        self.status_card.pack(fill="both", expand=True, padx=20, pady=10)

        # Status Section Header
        self.card_header = ctk.CTkLabel(
            self.status_card,
            text="System Integration & Health Status",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.card_header.pack(anchor="w", padx=20, pady=(15, 10))

        # API Status Row
        self.api_status_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.api_status_frame.pack(fill="x", padx=20, pady=5)
        
        self.api_title = ctk.CTkLabel(
            self.api_status_frame,
            text="Backend API Service:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=180,
            anchor="w"
        )
        self.api_title.pack(side="left")
        
        self.api_status_val = ctk.CTkLabel(
            self.api_status_frame,
            text="⏳ Checking...",
            font=ctk.CTkFont(size=14),
            text_color="#FBBF24"
        )
        self.api_status_val.pack(side="left", padx=10)

        # Database Status Row
        self.db_status_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        self.db_status_frame.pack(fill="x", padx=20, pady=5)
        
        self.db_title = ctk.CTkLabel(
            self.db_status_frame,
            text="PostgreSQL 18 Database:",
            font=ctk.CTkFont(size=14, weight="bold"),
            width=180,
            anchor="w"
        )
        self.db_title.pack(side="left")
        
        self.db_status_val = ctk.CTkLabel(
            self.db_status_frame,
            text="⏳ Checking...",
            font=ctk.CTkFont(size=14),
            text_color="#FBBF24"
        )
        self.db_status_val.pack(side="left", padx=10)

        # Detailed Diagnostic Message Box
        self.diagnostic_box = ctk.CTkTextbox(
            self.status_card,
            height=120,
            font=ctk.CTkFont(family="Consolas", size=12),
            state="disabled"
        )
        self.diagnostic_box.pack(fill="x", padx=20, pady=(15, 15))

        # Control Bar
        self.btn_check = ctk.CTkButton(
            self,
            text="🔄 Re-check Connection",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.trigger_health_check,
            height=40
        )
        self.btn_check.pack(pady=(5, 20))

    def trigger_health_check(self):
        """Runs the API check in a background thread to prevent UI lockup."""
        self.api_status_val.configure(text="⏳ Querying API...", text_color="#FBBF24")
        self.db_status_val.configure(text="⏳ Querying Database...", text_color="#FBBF24")
        self._update_diagnostic("Contacting backend API at http://127.0.0.1:8000/health...\n")
        
        threading.Thread(target=self._run_async_check, daemon=True).start()

    def _run_async_check(self):
        health = self.api_client.get_health()
        self.after(0, self._render_health_results, health)

    def _render_health_results(self, health: dict):
        api_ok = health.get("api_service") == "running"
        db_info = health.get("database", {})
        db_ok = db_info.get("database_connected", False)

        # Render API indicator
        if api_ok:
            self.api_status_val.configure(text="✅ Online (FastAPI localhost:8000)", text_color="#34D399")
        else:
            self.api_status_val.configure(text="❌ Offline (Check main_api.py)", text_color="#F87171")

        # Render Database indicator
        if db_ok:
            self.db_status_val.configure(text="✅ Connected (PostgreSQL 18)", text_color="#34D399")
        else:
            self.db_status_val.configure(text="❌ Disconnected", text_color="#F87171")

        # Update diagnostics display
        diag_msg = (
            f"Overall Status: {health.get('status', 'Unknown')}\n"
            f"API Status: {health.get('api_service', 'Unknown')}\n"
            f"Database Message: {db_info.get('message', 'No details available')}\n"
        )
        self._update_diagnostic(diag_msg)

    def _update_diagnostic(self, text: str):
        self.diagnostic_box.configure(state="normal")
        self.diagnostic_box.delete("1.0", "end")
        self.diagnostic_box.insert("1.0", text)
        self.diagnostic_box.configure(state="disabled")

if __name__ == "__main__":
    app = PharmacyManagementApp()
    app.mainloop()
