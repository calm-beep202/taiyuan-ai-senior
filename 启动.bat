@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   Taiyuan AI Senior - Launcher
echo ============================================
echo.
start "web-service" cmd /k "python app\web.py"
start "cpolar-tunnel" /D "C:\Program Files\cpolar" cmd /k "cpolar.exe http -log stdout -log-level INFO 8000"
echo Two windows opened:
echo   1. [web-service]   - keep it open
echo   2. [cpolar-tunnel] - public URL is in the "Tunnel established" line
echo.
echo Keep BOTH windows open. Closing them kills the public link.
echo.
pause
