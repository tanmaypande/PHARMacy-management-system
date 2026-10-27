"""
Main Application Launcher for Pharmacy Management System.
Orchestrates both the FastAPI backend service and the CustomTkinter desktop UI.
If the backend is not running, it automatically spawns it and shuts it down on exit.
"""
import sys
import os
import time
import subprocess
import urllib.request
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


def is_backend_healthy() -> bool:
    url = f"http://{settings.API_HOST}:{settings.API_PORT}/health"
    try:
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def main():
    backend_proc = None
    started_by_us = False

    print("=" * 60)
    print(" MediCare Pharmacy Management System — Launching...")
    print("=" * 60)

    # 1. Check if backend is already running
    if is_backend_healthy():
        print(f"[OK] Backend API is already running at http://{settings.API_HOST}:{settings.API_PORT}")
    else:
        print(f"[*] Starting FastAPI backend on http://{settings.API_HOST}:{settings.API_PORT}...")
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main_api:app",
            "--host",
            str(settings.API_HOST),
            "--port",
            str(settings.API_PORT),
        ]
        backend_proc = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))
        started_by_us = True

        # Wait for backend to become healthy (up to 12 seconds)
        print("[*] Waiting for backend and database connection...", end="", flush=True)
        ready = False
        for _ in range(24):
            time.sleep(0.5)
            print(".", end="", flush=True)
            if is_backend_healthy():
                ready = True
                break
        print()

        if not ready:
            print("[ERROR] FastAPI backend failed to start within timeout.")
            if backend_proc:
                backend_proc.terminate()
            sys.exit(1)

        print("[OK] Backend connected to PostgreSQL 18 and ready!")

    # 2. Launch the CustomTkinter UI
    print("[*] Launching Desktop UI...")
    try:
        from app.ui.main_window import MainWindow

        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        if started_by_us and backend_proc:
            print("[*] Stopping background backend service...")
            backend_proc.terminate()
            try:
                backend_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                backend_proc.kill()
            print("[OK] System shutdown complete.")


if __name__ == "__main__":
    main()
