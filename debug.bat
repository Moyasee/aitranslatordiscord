@echo off
echo Running AI Translator for Discord diagnostics...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Run the diagnostics script
python debug.py

echo.
echo Press any key to exit...
pause >nul 