@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   BusTrack AI - Launching Application
echo ============================================================
echo.

:: Check installation
if not exist "%~dp0backend\venv" (
    echo [WARNING] Backend virtual environment not found!
    echo Please run install.bat first to set up all dependencies.
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0frontend\node_modules" (
    echo [WARNING] Frontend node_modules not found!
    echo Please run install.bat first to set up all dependencies.
    echo.
    pause
    exit /b 1
)

echo [1/2] Starting Flask Backend Server (Port 5000)...
start "BusTrack AI - Backend" cmd /k "title BusTrack AI - Backend && cd /d "%~dp0backend" && call venv\Scripts\activate.bat && python app.py"

echo [2/2] Starting Vite Frontend Server (Port 5173)...
start "BusTrack AI - Frontend" cmd /k "title BusTrack AI - Frontend && cd /d "%~dp0frontend" && npm run dev"

echo.
echo Waiting 4 seconds for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening dashboard in browser...
start http://localhost:5173

echo.
echo ============================================================
echo   APPLICATION RUNNING!
echo   - Backend:  http://localhost:5000
echo   - Frontend: http://localhost:5173
echo ============================================================
echo.
echo Press any key to close this launcher window (servers keep running in their own windows).
pause >nul
