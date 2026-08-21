import time
import ctypes
from backend.logger import setup_logger
from backend.tools.registry import registry
import pyautogui

logger = setup_logger(__name__)

ALLOWED_KEYS = {
    "enter", "tab", "esc", "backspace", "space", 
    "up", "down", "left", "right"
}

user32 = ctypes.windll.user32
WM_CHAR = 0x0102

def get_focused_child_hwnd():
    foreground_hwnd = user32.GetForegroundWindow()
    if not foreground_hwnd:
        return 0
    fg_thread = user32.GetWindowThreadProcessId(foreground_hwnd, None)
    current_thread = ctypes.windll.kernel32.GetCurrentThreadId()
    if fg_thread != current_thread:
        user32.AttachThreadInput(current_thread, fg_thread, True)
        focused_hwnd = user32.GetFocus()
        user32.AttachThreadInput(current_thread, fg_thread, False)
        return focused_hwnd if focused_hwnd else foreground_hwnd
    else:
        focused_hwnd = user32.GetFocus()
        return focused_hwnd if focused_hwnd else foreground_hwnd

@registry.register(requires_confirmation=False, risk_level="LOW")
def system_type_text(text: str) -> dict:
    """Type text globally using the system keyboard (useful for native OS apps like Notepad)."""
    try:
        logger.info(f"Typing text (background mode)...")
        
        target_hwnd = get_focused_child_hwnd()
        
        class_name = ctypes.create_unicode_buffer(256)
        if target_hwnd:
            user32.GetClassNameW(target_hwnd, class_name, 256)
            
        is_uwp = class_name.value in ("ApplicationFrameWindow", "Windows.UI.Core.CoreWindow", "CalcFrame")
        
        if not target_hwnd or is_uwp:
            logger.warning(f"Using pyautogui global typing (HWND={target_hwnd}, UWP={is_uwp}).")
            pyautogui.write(text, interval=0.04)
        else:
            for char in text:
                user32.PostMessageW(target_hwnd, WM_CHAR, ord(char), 0)
                time.sleep(0.04)

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
