@echo off
REM Launch the outreach tool: start the server and open the dashboard. Double-click to run.
setlocal
cd /d "%~dp0backend"

if not exist "..\frontend\dist\index.html" (
  echo Dashboard not built yet. Please run setup.bat first.
  pause
  exit /b 1
)

echo Starting the outreach tool at http://127.0.0.1:8000 ...
start "outreach-tool-server" cmd /c "python -m uvicorn app.main:app --port 8000"

REM give the server a moment to boot, then open the browser
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000"

echo.
echo The dashboard should now be open in your browser.
echo Keep the "outreach-tool-server" window open while you work.
echo Close that window to stop the tool.
