import winreg
import sys
import os
from pathlib import Path

APP_NAME = "JARVIS_Assistant"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_pythonw_path() -> str:
    """Returns the absolute path to pythonw.exe in the current virtual environment or system."""
    executable = sys.executable
    if executable.lower().endswith('python.exe'):
        pythonw = executable[:-4] + 'w.exe'
        if os.path.exists(pythonw):
            return pythonw
    return executable

def get_startup_command() -> str:
    """Returns the command used to launch JARVIS in background mode at startup."""
    pythonw = get_pythonw_path()
    project_root = Path(__file__).parent.parent.absolute()
    return f'"{pythonw}" -m backend.main --background'

def install_startup():
    """Adds JARVIS to the Windows startup registry for the current user."""
    try:
        command = get_startup_command()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        print("\n[STARTUP] JARVIS installed to Windows startup.")
        print(f"Command: {command}\n")
    except Exception as e:
        print(f"\n[STARTUP ERROR] Failed to install startup: {e}\n")

def remove_startup():
    """Removes JARVIS from the Windows startup registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, APP_NAME)
        print("\n[STARTUP] JARVIS removed from Windows startup.\n")
    except FileNotFoundError:
        print("\n[STARTUP] JARVIS is not in Windows startup. Nothing to remove.\n")
    except Exception as e:
        print(f"\n[STARTUP ERROR] Failed to remove startup: {e}\n")

def get_startup_status():
    """Checks if JARVIS is in the Windows startup registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            print("\nJARVIS Startup Status")
            print("-" * 25)
            print("Startup enabled: YES")
            print(f"Startup location: HKCU\\{REG_PATH}")
            print(f"Background command: {value}")
            print("-" * 25 + "\n")
            return True
    except FileNotFoundError:
        print("\nJARVIS Startup Status")
        print("-" * 25)
        print("Startup enabled: NO")
        print("-" * 25 + "\n")
        return False
    except Exception as e:
        print(f"\n[STARTUP ERROR] Failed to query startup status: {e}\n")
        return False
