@echo off
echo Setting up AI Translator for Discord...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Create sounds directory if it doesn't exist
if not exist sounds mkdir sounds

REM Generate notification sounds
echo Generating notification sounds...
python generate_sounds.py

REM Create application icon
echo Creating application icon...
python create_icon.py

echo Setup complete!
echo.
echo You can now run the application by executing 'python main.py'
echo Or build the executable by running 'python build.py'
echo.
echo Press any key to run the application...
pause >nul

python main.py 