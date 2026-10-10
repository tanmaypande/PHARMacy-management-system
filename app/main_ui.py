import customtkinter as ctk
import requests
import threading

class PharmacyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Q12 Accessibility: Minimalist UI, Dark Mode Default
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.title("Pharmacy Management System - UI Prototype")
        self.geometry("800x600")
        
        self.label = ctk.CTkLabel(self, text="Pharmacy Desktop UI initializing...", font=("Arial", 20, "bold"))
        self.label.pack(pady=40)
        
        self.status_label = ctk.CTkLabel(self, text="Checking API connection...", text_color="yellow")
        self.status_label.pack(pady=20)
        
        self.btn_refresh = ctk.CTkButton(self, text="Refresh Connection", command=self.check_api)
        self.btn_refresh.pack(pady=10)

        # Check API status asynchronously
        self.check_api()

    def check_api(self):
        self.status_label.configure(text="Checking API connection...", text_color="yellow")
        threading.Thread(target=self._ping_api, daemon=True).start()

    def _ping_api(self):
        try:
            response = requests.get("http://127.0.0.1:8000/health", timeout=3)
            if response.status_code == 200:
                self.status_label.configure(text="✅ Connected to Backend API", text_color="green")
            else:
                self.status_label.configure(text=f"❌ API Error: {response.status_code}", text_color="red")
        except requests.exceptions.RequestException:
            self.status_label.configure(text="❌ Cannot connect to Backend API (Is it running?)", text_color="red")

if __name__ == "__main__":
    app = PharmacyApp()
    app.mainloop()
