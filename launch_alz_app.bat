@echo off
setlocal EnableExtensions

REM ALZ Memory Assistant Windows launcher.
REM Double-click this file from Windows. It starts/keeps the WSL backend alive,
REM waits until the local site responds, then opens the login page.

set "APP_DIR=/root/alz-memory-assistant"
set "APP_URL=http://127.0.0.1:8000/login"

echo [1/3] Checking ALZ Memory Assistant backend...
curl -s -o NUL "%APP_URL%" >NUL 2>NUL
if errorlevel 1 (
    echo Backend is not running. Starting a small WSL backend window...
    echo Please keep the "ALZ Backend" window open while using the app.
    start "ALZ Backend - keep open" /min wsl.exe --cd "%APP_DIR%" -- bash -lc "./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"
) else (
    echo Backend is already running.
)

echo [2/3] Waiting for http://127.0.0.1:8000/login ...
for /l %%i in (1,1,20) do (
    curl -s -o NUL "%APP_URL%" >NUL 2>NUL
    if not errorlevel 1 goto OPEN_APP
    timeout /t 1 /nobreak >NUL
)

echo.
echo ERROR: The local web service did not become reachable.
echo Try running this in WSL:
echo   cd /root/alz-memory-assistant
echo   ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
pause
exit /b 1

:OPEN_APP
echo [3/3] Opening browser...

REM Prefer Google Chrome in app-window mode, then fall back to the default browser.
REM Keep 127.0.0.1 instead of localhost to avoid local DNS/proxy issues.
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if exist "%CHROME%" (
    start "" "%CHROME%" --app="%APP_URL%"
) else (
    explorer.exe "%APP_URL%"
)
exit /b 0
