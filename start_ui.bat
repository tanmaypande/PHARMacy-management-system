@echo off
setlocal
title MediCare Desktop UI
cd /d "%~dp0"
echo =========================================================
echo   Starting MediCare Desktop UI (CustomTkinter)
echo =========================================================
echo.
"%~dp0.venv\Scripts\python.exe" -m app.main_ui
pause
