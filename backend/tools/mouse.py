from backend.logger import setup_logger
from backend.tools.registry import registry
import pyautogui

logger = setup_logger(__name__)

# Basic screen bounds validation
try:
    SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
except Exception:
    SCREEN_WIDTH, SCREEN_HEIGHT = 1920, 1080  # Safe fallback for headless/CI

def _validate_coordinates(x: int, y: int) -> bool:
    if x < 0 or y < 0 or x > SCREEN_WIDTH or y > SCREEN_HEIGHT:
        return False
    return True

@registry.register(requires_confirmation=False, risk_level="LOW")
def move_mouse(x: int, y: int) -> dict:
    """Move the mouse cursor to absolute screen coordinates (x, y)."""
    if not _validate_coordinates(x, y):
        return {
            "success": False,
            "action": "move_mouse",
            "error": f"Coordinates ({x}, {y}) are out of screen bounds."
        }
    try:
        logger.info(f"Moving mouse to ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.25)
        return {
            "success": True,
            "action": "move_mouse",
            "x": x,
            "y": y,
            "message": f"Mouse moved to ({x}, {y})."
        }
    except Exception as e:
        logger.error(f"Failed to move mouse: {e}")
        return {
            "success": False,
            "action": "move_mouse",
            "error": f"Unable to move mouse: {str(e)}"
        }

@registry.register(requires_confirmation=False, risk_level="LOW")
def click_mouse(button: str = "left") -> dict:
    """Click the mouse button ('left', 'middle', 'right') at the current cursor position."""
    normalized_button = button.lower()
    if normalized_button not in ["left", "middle", "right"]:
        return {"success": False, "error": f"Invalid mouse button: {button}"}
        
    try:
        logger.info(f"Clicking mouse button: {normalized_button}")
        pyautogui.click(button=normalized_button)
        return {
            "success": True,
            "action": "click_mouse",
            "message": f"Mouse '{normalized_button}' click completed."
        }
    except Exception as e:
        return {"success": False, "error": f"Mouse click failed: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def double_click_mouse(button: str = "left") -> dict:
    """Double-click the mouse button at the current cursor position."""
    normalized_button = button.lower()
    if normalized_button not in ["left", "middle", "right"]:
        return {"success": False, "error": f"Invalid mouse button: {button}"}
        
    try:
        logger.info(f"Double-clicking mouse button: {normalized_button}")
        pyautogui.doubleClick(button=normalized_button)
        return {
            "success": True,
            "action": "double_click_mouse",
            "message": f"Mouse '{normalized_button}' double-click completed."
        }
    except Exception as e:
        return {"success": False, "error": f"Mouse double-click failed: {str(e)}"}
