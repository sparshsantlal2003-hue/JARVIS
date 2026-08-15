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
    }
}

# Alias mapping for natural language variations
ALIAS_MAP = {
    "notepad": "notepad",
    "calc": "calculator",
    "calculator": "calculator",
    "paint": "paint",
    "mspaint": "paint",
    "explorer": "explorer",
    "folder": "explorer",
}

@registry.register
def launch_application(application_name: str) -> dict:
    """Launch a safe, explicitly allowlisted Windows application.
    
    Args:
        application_name: The name of the application to launch (e.g., 'notepad', 'calculator', 'paint').
    """
    # Normalize input
    normalized_name = application_name.strip().lower()
    if normalized_name.endswith('.exe'):
        normalized_name = normalized_name[:-4]
    
    # Resolve alias
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
        # Launching without shell=True for security
        # Using subprocess.Popen to launch detached without blocking the agent
        logger.info(f"Launching application: {resolved_key} ({executable})")
        subprocess.Popen([executable], shell=False)
        time.sleep(1.5)  # Wait for application to gain focus before returning
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
