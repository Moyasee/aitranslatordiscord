@echo off
echo Starting AI Translator for Discord...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Run the application
python main.py

:: If the application exits with an error, show a message
if %errorlevel% neq 0 (
    echo.
    echo The application exited with an error. Please check the log file for details.
    echo Log file: translator_debug.log
    pause
) 