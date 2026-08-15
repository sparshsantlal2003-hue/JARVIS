import os
import pathlib
from backend.logger import setup_logger
from backend.tools.registry import registry

logger = setup_logger(__name__)

# Basic safety setup
USER_HOME = pathlib.Path(os.path.expanduser("~")).resolve()

# Extremely explicit blocklist for windows
FORBIDDEN_DIRECTORIES = [
    "windows",
    "system32",
    "program files",
    "program files (x86)",
    "appdata"
]

def _is_safe_path(requested_path: str) -> bool:
    """Validate that a path is safe to access."""
    try:
        # Resolve resolves symlinks and normalizes ../
        target = pathlib.Path(requested_path).resolve()
        
        # 1. Must be within the user's home directory
        if not str(target).startswith(str(USER_HOME)):
            logger.warning(f"Path traversal attempt or outside home dir blocked: {target}")
            return False
            
        # 2. Must not contain forbidden Windows directories
        target_lower = str(target).lower()
        for forbidden in FORBIDDEN_DIRECTORIES:
            if f"\\{forbidden}\\" in target_lower or target_lower.endswith(f"\\{forbidden}"):
                logger.warning(f"Access to forbidden directory blocked: {forbidden}")
                return False
                
        return True
    except Exception as e:
        logger.error(f"Path validation error: {e}")
        return False

@registry.register(requires_confirmation=False, risk_level="LOW")
def list_directory(path: str) -> dict:
    """List files and folders in a safe directory."""
    if not _is_safe_path(path):
        return {"success": False, "error": "Access denied. Path is outside allowed directories or protected."}
        
    try:
        entries = os.listdir(path)
        return {
            "success": True,
            "path": path,
            "entries": entries,
            "message": f"Successfully listed {len(entries)} items."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to list directory: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def create_directory(path: str) -> dict:
    """Create a directory at the specified safe path."""
    if not _is_safe_path(path):
        return {"success": False, "error": "Access denied. Path is outside allowed directories or protected."}
        
    try:
        os.makedirs(path, exist_ok=True)
        return {
            "success": True,
            "path": path,
            "message": "Directory created successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to create directory: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def read_text_file(path: str) -> dict:
    """Read the contents of a safe text file."""
    if not _is_safe_path(path):
        return {"success": False, "error": "Access denied. Path is outside allowed directories or protected."}
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {
            "success": True,
            "path": path,
            "content": content,
            "message": "File read successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to read file: {str(e)}"}

@registry.register(requires_confirmation=True, risk_level="MEDIUM")
def write_text_file(path: str, content: str) -> dict:
    """Write text content to a safe file path. Creates file if missing, overwrites if exists."""
    if not _is_safe_path(path):
        return {"success": False, "error": "Access denied. Path is outside allowed directories or protected."}
        
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "success": True,
            "path": path,
            "message": "File written successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to write file: {str(e)}"}

import subprocess

@registry.register(requires_confirmation=False, risk_level="LOW")
def open_path_in_ui(path: str) -> dict:
    """Open a file or folder in the native Windows UI (File Explorer or default application) so the user can see it."""
    if not _is_safe_path(path):
        return {"success": False, "error": "Access denied. Path is outside allowed directories or protected."}
        
    try:
        if not os.path.exists(path):
            return {"success": False, "error": f"Path does not exist: {path}"}
            
        logger.info(f"Opening path in UI: {path}")
        os.startfile(path)
        return {
            "success": True,
            "path": path,
            "message": "Successfully opened in Windows UI."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to open path: {str(e)}"}
