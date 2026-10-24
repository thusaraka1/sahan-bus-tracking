@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   BusTrack AI - Automated Installation Script (Windows)
echo ============================================================
echo.

:: 1. Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in your system PATH.
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo   Found: %%i

:: 2. Check Node.js
echo.
echo [2/4] Checking Node.js and npm...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in your system PATH.
    echo Please install Node.js 18 or higher from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node --version') do echo   Found Node: %%i
for /f "tokens=*" %%i in ('npm --version') do echo   Found npm:  v%%i

:: 3. Setup Backend
echo.
echo [3/4] Setting up Python Backend...
cd /d "%~dp0backend"

if not exist "venv" (
    echo   Creating Python virtual environment in backend\venv...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo   Activating virtual environment...
call venv\Scripts\activate.bat

echo   Installing backend dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install backend dependencies.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        echo   Copying .env.example to .env...
        copy .env.example .env >nul
        echo   [NOTE] Created backend\.env. Please update it with your HiveMQ credentials if using real IoT devices.
    )
)

if not exist "data" (
    mkdir data
)

:: 4. Setup Frontend
echo.
echo [4/4] Setting up Frontend...
cd /d "%~dp0frontend"
echo   Installing Node packages (this may take 1-2 minutes)...
call npm install
if errorlevel 1 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
)

cd /d "%~dp0"

echo.
echo ============================================================
echo   INSTALLATION COMPLETED SUCCESSFULLY!
echo ============================================================
echo.
echo To run the application:
echo   Double-click run.bat (or execute .\run.bat in terminal)
echo.
pause
