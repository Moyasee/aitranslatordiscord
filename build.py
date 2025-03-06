import os
import subprocess
import sys
import shutil

def build_executable():
    """Build the executable with PyInstaller."""
    print("Building AI Translator for Discord...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create a simple icon file if it doesn't exist
    if not os.path.exists("icon.ico"):
        print("Creating a placeholder icon...")
        try:
            subprocess.check_call([sys.executable, "create_icon.py"])
        except Exception as e:
            print(f"Warning: Could not create icon: {e}")
            # Create an empty file as fallback
            with open("icon.ico", "wb") as f:
                pass
    
    # Generate sound files if they don't exist
    if not os.path.exists("sounds/start.wav") or not os.path.exists("sounds/complete.wav"):
        print("Generating sound files...")
        try:
            subprocess.check_call([sys.executable, "generate_sounds.py"])
        except Exception as e:
            print(f"Warning: Could not generate sound files: {e}")
    
    # Create a spec file for PyInstaller
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.'), ('sounds', 'sounds'), ('config.json', '.')],
    hiddenimports=['win32api', 'win32con', 'win32gui', 'win32clipboard', 'playsound', 'keyboard', 'PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AITranslatorForDiscord',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    uac_admin=True,
)
    """
    
    with open("translator.spec", "w") as f:
        f.write(spec_content)
    
    # Build the executable
    print("Building executable with PyInstaller...")
    try:
        subprocess.check_call([
            "pyinstaller",
            "--clean",
            "translator.spec"
        ])
        
        print("\nBuild complete! The executable is in the 'dist' folder.")
        print("You can now run 'dist/AITranslatorForDiscord.exe'")
        
        # Create a shortcut to the executable on the desktop
        try:
            import win32com.client
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "AI Translator for Discord.lnk")
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = os.path.abspath("dist/AITranslatorForDiscord.exe")
            shortcut.WorkingDirectory = os.path.abspath("dist")
            shortcut.IconLocation = os.path.abspath("icon.ico")
            shortcut.save()
            
            print(f"Created shortcut on desktop: {shortcut_path}")
        except Exception as e:
            print(f"Warning: Could not create desktop shortcut: {e}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_executable() 