"""
Desktop UI Entry Point for the Pharmacy Management System.
Launches the full CustomTkinter user interface with Q12 Accessibility
and decoupled HTTP communication to the FastAPI backend.
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path regardless of execution context
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.ui.main_window import MainWindow

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
