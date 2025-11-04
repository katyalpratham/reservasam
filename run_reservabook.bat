@echo off
setlocal
title Reservabook - Starting Backend
cd /d "%~dp0"

echo ================================================
echo    RESERVABOOK - Online Booking System
echo ================================================
echo.

REM Check Python
python --version >nul 2>&1 || (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Check MySQL connection
echo Checking MySQL connection...
python -c "import mysql.connector; mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='KATYAL0786')" >nul 2>&1 || (
    echo [WARNING] Cannot connect to MySQL. Make sure MySQL is running.
    echo Continuing anyway...
)

echo.
echo Installing Python dependencies...
cd BACKEND
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Starting backend server...
echo Backend will run on http://127.0.0.1:5500
echo.
echo Open your HTML file in a browser to use the booking system.
echo.
start "Reservabook Backend" powershell -NoExit -Command "cd '%CD%'; python reservabook_server.py"

echo.
echo Backend server started in a new window.
echo Keep that window open while using the application.
echo.
pause

