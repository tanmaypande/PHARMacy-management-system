"""
Desktop UI Entry Point for the Pharmacy Management System.
Launches the full CustomTkinter user interface with Q12 Accessibility
and decoupled HTTP communication to the FastAPI backend.
"""
from app.ui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
