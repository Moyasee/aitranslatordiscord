import os
import sys
import platform
import subprocess
import json
import keyboard
import ctypes
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon

def check_system():
    """Check system information."""
    print("=== System Information ===")
    print(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"Python: {platform.python_version()}")
    print(f"Architecture: {platform.architecture()}")
    print(f"Machine: {platform.machine()}")
    print(f"Processor: {platform.processor()}")
    print()

def check_dependencies():
    """Check if all required dependencies are installed."""
    print("=== Checking Dependencies ===")
    dependencies = [
        "PyQt5", "keyboard", "pyperclip", "requests", 
        "playsound", "pywin32", "pillow"
    ]
    
    for dep in dependencies:
        try:
            if dep == "pywin32":
                import win32api
                print(f"✓ {dep} is installed")
            else:
                __import__(dep)
                print(f"✓ {dep} is installed")
        except ImportError:
            print(f"✗ {dep} is NOT installed")
    print()

def check_files():
    """Check if all required files exist."""
    print("=== Checking Files ===")
    required_files = [
        "main.py", "config.json", "icon.ico", 
        "sounds/start.wav", "sounds/complete.wav"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} exists")
        else:
            print(f"✗ {file} does NOT exist")
    print()

def check_config():
    """Check if the configuration file is valid."""
    print("=== Checking Configuration ===")
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            print("✓ config.json is valid JSON")
            
            # Check API key
            api_key = config.get("api", {}).get("api_key", "")
            if api_key and api_key != "YOUR_API_KEY_HERE":
                print("✓ API key is set")
            else:
                print("✗ API key is NOT set")
            
            # Check shortcuts
            shortcuts = config.get("shortcuts", {})
            print(f"Translate and send shortcut: {shortcuts.get('translate_and_send', 'Not set')}")
            print(f"Translate selected shortcut: {shortcuts.get('translate_selected', 'Not set')}")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"✗ Error reading config.json: {e}")
    print()

def check_keyboard_shortcuts():
    """Check if keyboard shortcuts can be registered."""
    print("=== Checking Keyboard Shortcuts ===")
    try:
        # Try to register a test shortcut
        test_triggered = False
        
        def test_callback():
            nonlocal test_triggered
            test_triggered = True
            print("✓ Test shortcut triggered successfully")
        
        print("Registering test shortcut (ctrl+alt+d)...")
        keyboard.add_hotkey("ctrl+alt+d", test_callback)
        
        print("Please press CTRL+ALT+D to test keyboard shortcuts...")
        print("(Waiting for 10 seconds...)")
        
        # Wait for the shortcut to be triggered
        for i in range(10):
            if test_triggered:
                break
            sys.stdout.write(".")
            sys.stdout.flush()
            keyboard.read_event(suppress=False)
        
        if not test_triggered:
            print("\n✗ Test shortcut was NOT triggered within the timeout period")
        
        # Clean up
        keyboard.unhook_all()
    except Exception as e:
        print(f"✗ Error testing keyboard shortcuts: {e}")
    print()

def check_system_tray():
    """Check if the system tray is available."""
    print("=== Checking System Tray ===")
    try:
        app = QApplication(sys.argv)
        tray = QSystemTrayIcon()
        
        if QSystemTrayIcon.isSystemTrayAvailable():
            print("✓ System tray is available")
        else:
            print("✗ System tray is NOT available")
        
        if QSystemTrayIcon.supportsMessages():
            print("✓ System tray supports messages")
        else:
            print("✗ System tray does NOT support messages")
    except Exception as e:
        print(f"✗ Error checking system tray: {e}")
    print()

def check_admin_privileges():
    """Check if the script is running with administrator privileges."""
    print("=== Checking Administrator Privileges ===")
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if is_admin:
            print("✓ Running with administrator privileges")
        else:
            print("✗ NOT running with administrator privileges")
            print("  Some keyboard shortcuts may not work without admin rights")
    except Exception as e:
        print(f"✗ Error checking admin privileges: {e}")
    print()

def run_diagnostics():
    """Run all diagnostic checks."""
    print("=== AI Translator for Discord Diagnostics ===")
    print()
    
    check_system()
    check_dependencies()
    check_files()
    check_config()
    check_admin_privileges()
    check_system_tray()
    check_keyboard_shortcuts()
    
    print("=== Diagnostics Complete ===")
    print("If you're experiencing issues, please check the log file: translator_debug.log")
    print("You can also try running the application with administrator privileges.")

if __name__ == "__main__":
    run_diagnostics() 