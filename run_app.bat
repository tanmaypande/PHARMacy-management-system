@echo off
setlocal
title MediCare Pharmacy Management System
cd /d "%~dp0"

echo =========================================================
echo   Starting MediCare Pharmacy Management System (PMS)
echo =========================================================
echo.

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment python was not found at:
    echo "%~dp0.venv\Scripts\python.exe"
    echo.
    echo Please make sure the .venv directory exists in this folder.
    echo.
    pause
    exit /b 1
)

echo Starting MediCare PMS application...
"%~dp0.venv\Scripts\python.exe" -m app.main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTICE] Application closed with return code %ERRORLEVEL%.
    pause
)
