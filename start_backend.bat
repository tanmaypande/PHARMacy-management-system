@echo off
setlocal
title MediCare Backend API
cd /d "%~dp0"
echo =========================================================
echo   Starting MediCare Backend API (FastAPI)
echo =========================================================
echo.
"%~dp0.venv\Scripts\python.exe" -m uvicorn app.main_api:app --reload
pause
