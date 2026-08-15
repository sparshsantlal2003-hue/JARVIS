from backend.logger import setup_logger
from backend.tools.registry import registry
from backend.tools.browser.browser_manager import browser_manager

logger = setup_logger(__name__)

@registry.register(requires_confirmation=False, risk_level="LOW")
def click_element(target: str) -> dict:
    """Click an element on the page using text or a CSS selector."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        logger.info(f"Attempting to click: {target}")
        
        # We try to find by text first, which is safest/most natural
        locator = page.get_by_text(target, exact=False).first
        
        if not locator.is_visible(timeout=1000):
            # Fallback to CSS selector if text not found
            locator = page.locator(target).first
            if not locator.is_visible(timeout=1000):
                return {"success": False, "error": f"Element '{target}' not found or not visible."}
        
        locator.click(timeout=5000)
        return {"success": True, "target": target, "message": f"Successfully clicked '{target}'."}
        
    except Exception as e:
        logger.error(f"Click failed: {e}")
        return {"success": False, "error": f"Failed to click '{target}': {str(e)}"}

@registry.register(requires_confirmation=True, risk_level="MEDIUM")
def fill_field(target: str, text: str) -> dict:
    """Fill a text input field identified by its label, placeholder, or selector. Password inputs are rejected."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        logger.info(f"Attempting to fill field: {target}")
        
        locator = page.get_by_label(target).first
        if not locator.is_visible(timeout=1000):
            locator = page.get_by_placeholder(target).first
            if not locator.is_visible(timeout=1000):
                locator = page.locator(target).first
                if not locator.is_visible(timeout=1000):
                    return {"success": False, "error": f"Field '{target}' not found or not visible."}

        input_type = locator.get_attribute("type")
        if input_type and input_type.lower() == "password":
            return {"success": False, "error": "Blocked attempt to interact with a password field."}

        locator.fill(text, timeout=5000)
        return {"success": True, "target": target, "message": f"Successfully filled field '{target}'."}
        
    except Exception as e:
        return {"success": False, "error": f"Failed to fill field '{target}': {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def type_text(text: str) -> dict:
    """Type text directly into the page (wherever focus currently is)."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        page.keyboard.type(text)
        return {"success": True, "message": f"Typed text successfully."}
    except Exception as e:
        return {"success": False, "error": f"Failed to type text: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def scroll_page(direction: str = "down", amount: int = 800) -> dict:
    """Scroll the current page up or down."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        normalized_dir = direction.lower().strip()
        if normalized_dir not in ["up", "down"]:
            return {"success": False, "error": "Direction must be 'up' or 'down'."}
            
        if amount < 500:
            amount = 800
            
        sign = 1 if normalized_dir == "down" else -1
        page.evaluate(f"window.scrollBy(0, {sign * amount})")
        
        return {"success": True, "direction": normalized_dir, "amount": amount, "message": f"Scrolled {normalized_dir} by {amount}px."}
    except Exception as e:
        return {"success": False, "error": f"Failed to scroll: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def keyboard_action(key: str) -> dict:
    """Press a key on the keyboard in the browser (e.g., 'Enter', 'Space', 'Escape', 'ArrowDown')."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        allowed_keys = ['Enter', 'Tab', 'Escape', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Backspace', 'Delete', 'Home', 'End', 'PageUp', 'PageDown', 'Space', 'k', 'f', 'm', 'j', 'l', ' ']
        
        if key not in allowed_keys and len(key) > 1 and not key.isalnum():
            return {"success": False, "error": f"Key '{key}' is not permitted."}
            
        page.keyboard.press(key)
        return {"success": True, "action": "press_key", "key": key, "message": "Key pressed successfully."}
    except Exception as e:
        return {"success": False, "error": f"Failed to press key: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def finish_task(message: str) -> dict:
    """Use this tool explicitly to declare that you have successfully completed all the steps of the user's request. You MUST call this when you are done."""
    return {"success": True, "message": message, "task_finished": True}
