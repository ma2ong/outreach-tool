@echo off
REM One-time setup for the outreach tool. Double-click to run.
setlocal
cd /d "%~dp0"

echo === [1/3] Installing backend dependencies ===
cd backend
python -m pip install -r requirements.txt
if errorlevel 1 goto :err

echo === [2/3] Importing existing leads into the database ===
python -m app.migrate
if errorlevel 1 goto :err

echo === [3/3] Building the dashboard front-end ===
cd ..\frontend
call npm install
if errorlevel 1 goto :err
call npm run build
if errorlevel 1 goto :err

echo.
echo Setup complete. Double-click start.bat to launch the tool.
pause
exit /b 0

:err
echo.
echo Setup FAILED. Please check the messages above.
pause
exit /b 1
