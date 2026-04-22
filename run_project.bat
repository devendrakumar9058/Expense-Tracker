@echo off
echo ==========================================
echo   AI Expense Tracker - Professional Setup
echo ==========================================
echo.

:: Check if Python Launcher is installed
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python Launcher not found. Please install Python from python.org.
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
py -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo [2/3] Initializing...

echo [3/3] Launching Professional Dashboard...
py -m streamlit run app.py

pause
