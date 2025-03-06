@echo off
echo Running AI Translator for Discord with administrator privileges...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Run the application with administrator privileges
powershell -Command "Start-Process python -ArgumentList 'main.py' -Verb RunAs"

echo.
echo If a UAC prompt appears, please click "Yes" to grant administrator privileges.
echo This is required for the keyboard shortcuts to work properly.
echo.
echo The application will start in the system tray.
echo. 