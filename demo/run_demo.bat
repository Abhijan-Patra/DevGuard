@echo off
REM DevGuard 1-Click Demo Launcher for Windows CMD
title DevGuard Demo Launcher
echo ==========================================================
echo            DevGuard Demo ^& Presentation Launcher          
echo ==========================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo Select presentation mode:
echo   [1] Mock Live Server + Dashboard (Zero-dependency rehearsal)
echo   [2] Real DevGuard Backend + Dashboard (Requires local Ollama)
echo   [3] Dashboard Only (Fixture Mode)
echo.
set /p choice="Enter choice [1-3] (Default: 1): "

if "%choice%"=="2" goto live
if "%choice%"=="3" goto uionly
goto mock

:mock
echo.
echo [*] Launching Mock Live Server in background...
start "DevGuard Mock Server" /min python demo\mock_live_server.py --port 8765
timeout /t 2 >nul
echo [*] Launching Streamlit Operator Dashboard...
python -m streamlit run devguard\ui\app.py
goto end

:live
echo.
echo [*] Launching DevGuard Backend in background...
start "DevGuard Backend" /min python -m devguard
timeout /t 3 >nul
echo [*] Launching Streamlit Operator Dashboard...
python -m streamlit run devguard\ui\app.py
goto end

:uionly
echo.
echo [*] Launching Streamlit Operator Dashboard in Fixture Mode...
python -m streamlit run devguard\ui\app.py
goto end

:end
echo.
echo [DevGuard] Session ended.
