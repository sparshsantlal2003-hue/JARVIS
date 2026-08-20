import time
import subprocess
from backend.logger import setup_logger
from backend.tools.registry import registry

logger = setup_logger(__name__)

# Explicit allowlist of safe Windows applications
APPLICATION_REGISTRY = {
    "notepad": {
        "executable": "notepad.exe",
        "description": "Windows Notepad text editor"
    },
    "calculator": {
        "executable": "calc.exe",
        "description": "Windows Calculator"
    },
    "paint": {
        "executable": "mspaint.exe",
        "description": "Windows Paint image editor"
    },
    "explorer": {
        "executable": "explorer.exe",
        "description": "Windows File Explorer"
    },
    "brave": {
        "executable": r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        "description": "Brave Browser"
    },
    "chrome": {
        "executable": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "description": "Google Chrome Browser"
    },
    "edge": {
        "executable": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "description": "Microsoft Edge Browser"
    },
    "vscode": {
        "executable": "code",
        "description": "Visual Studio Code"
    },
    "spotify": {
        "executable": r"C:\Users\Sparsh\AppData\Roaming\Spotify\Spotify.exe",
        "description": "Spotify Music Player"
    },
    "vlc": {
        "executable": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        "description": "VLC Media Player"
    },
    "taskmgr": {
        "executable": "taskmgr.exe",
        "description": "Windows Task Manager"
    },
    "cmd": {
        "executable": "cmd.exe",
        "description": "Windows Command Prompt"
    },
    "powershell": {
        "executable": "powershell.exe",
        "description": "Windows PowerShell"
    },
    "wordpad": {
        "executable": "wordpad.exe",
        "description": "Windows WordPad"
    },
    "snipping": {
        "executable": "SnippingTool.exe",
        "description": "Snipping Tool (screenshot)"
    },
}

# Alias mapping for natural language variations
ALIAS_MAP = {
    # Notepad
    "notepad": "notepad",
    # Calculator
    "calc": "calculator",
    "calculator": "calculator",
    # Paint
    "paint": "paint",
    "mspaint": "paint",
    # Explorer
    "explorer": "explorer",
    "folder": "explorer",
    "file explorer": "explorer",
    "files": "explorer",
    # Brave
    "brave": "brave",
    "brave browser": "brave",
    # Chrome
    "chrome": "chrome",
    "google chrome": "chrome",
    # Edge
    "edge": "edge",
    "microsoft edge": "edge",
    # VSCode
    "vscode": "vscode",
    "vs code": "vscode",
    "visual studio code": "vscode",
    "code": "vscode",
    # Spotify
    "spotify": "spotify",
    "music": "spotify",
    # VLC
    "vlc": "vlc",
    "vlc player": "vlc",
    # Task Manager
    "taskmgr": "taskmgr",
    "task manager": "taskmgr",
    # CMD
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "cmd",
    # PowerShell
    "powershell": "powershell",
    "ps": "powershell",
    # WordPad
    "wordpad": "wordpad",
    # Snipping Tool
    "snipping": "snipping",
    "snipping tool": "snipping",
    "screenshot": "snipping",
}

@registry.register
def launch_application(application_name: str) -> dict:
    """Launch a safe, explicitly allowlisted Windows application.
    
    Args:
        application_name: The name of the application to launch (e.g., 'brave', 'notepad', 'calculator').
    """
    normalized_name = application_name.strip().lower()
    if normalized_name.endswith(".exe"):
        normalized_name = normalized_name[:-4]

    resolved_key = ALIAS_MAP.get(normalized_name)

    if not resolved_key or resolved_key not in APPLICATION_REGISTRY:
        logger.warning(f"Blocked attempt to launch unsupported application: {application_name}")
        return {
            "success": False,
            "application": application_name,
            "error": "Application is not in the allowed application registry."
        }

    app_info = APPLICATION_REGISTRY[resolved_key]
    executable = app_info["executable"]

    try:
        logger.info(f"Launching application: {resolved_key} ({executable})")
        subprocess.Popen([executable], shell=False)
        time.sleep(1.5)
        return {
            "success": True,
            "application": resolved_key.capitalize(),
            "message": f"{resolved_key.capitalize()} launched successfully."
        }
    except FileNotFoundError:
        logger.error(f"Executable not found for {resolved_key}: {executable}")
        return {
            "success": False,
            "application": resolved_key.capitalize(),
            "error": f"The executable '{executable}' was not found on this system."
        }
    except Exception as e:
        logger.error(f"Failed to launch {resolved_key}: {str(e)}")
        return {
            "success": False,
            "application": resolved_key.capitalize(),
            "error": f"Failed to launch application: {str(e)}"
        }
