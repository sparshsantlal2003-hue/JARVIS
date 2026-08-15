import time
from backend.logger import setup_logger
from backend.tools.registry import registry
import pyautogui

logger = setup_logger(__name__)

ALLOWED_KEYS = {
    "enter", "tab", "esc", "backspace", "space", 
    "up", "down", "left", "right"
}

@registry.register(requires_confirmation=False, risk_level="LOW")
def type_text(text: str) -> dict:
    """Type the given text using the keyboard."""
    try:
        logger.info(f"Typing text: {text}")
        # Add a small delay for safety and realistic typing speed
        pyautogui.write(text, interval=0.01)
        return {
            "success": True,
            "action": "type_text",
            "message": "Text entered successfully."
        }
    except Exception as e:
        logger.error(f"Failed to type text: {e}")
        return {
            "success": False,
            "action": "type_text",
            "error": f"Unable to send keyboard input: {str(e)}"
        }

@registry.register(requires_confirmation=False, risk_level="LOW")
def press_key(key: str) -> dict:
    """Press a single allowed navigation or control key."""
    normalized_key = key.lower()
    if normalized_key not in ALLOWED_KEYS:
        return {
            "success": False,
            "action": "press_key",
            "error": f"Key '{key}' is not in the allowed safe key list."
        }
        
    try:
        logger.info(f"Pressing key: {normalized_key}")
        pyautogui.press(normalized_key)
        return {
            "success": True,
            "action": "press_key",
            "message": f"Key '{normalized_key}' pressed successfully."
        }
    except Exception as e:
        logger.error(f"Failed to press key {normalized_key}: {e}")
        return {
            "success": False,
            "action": "press_key",
            "error": f"Unable to press key: {str(e)}"
        }
