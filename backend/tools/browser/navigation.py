from backend.logger import setup_logger
from backend.tools.registry import registry
from backend.tools.browser.browser_manager import browser_manager

logger = setup_logger(__name__)

FORBIDDEN_PROTOCOLS = ["file://", "ftp://", "chrome://", "brave://", "edge://", "javascript:", "data:"]

def is_safe_url(url: str) -> bool:
    normalized = url.lower().strip()
    for forbidden in FORBIDDEN_PROTOCOLS:
        if normalized.startswith(forbidden):
            return False
    return True

def ensure_protocol(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        return "https://" + url
    return url

@registry.register(requires_confirmation=False, risk_level="LOW")
def navigate(url: str) -> dict:
    """Navigate the browser to a specific URL."""
    if not is_safe_url(url):
        return {"success": False, "error": f"Invalid or unsafe URL protocol: {url}"}
        
    final_url = ensure_protocol(url)
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed or unavailable."}
            
        logger.info(f"Navigating to {final_url}")
        
        try:
            page.goto(final_url, wait_until="domcontentloaded", timeout=10000)
            return {
                "success": True,
                "url": page.url,
                "title": page.title(),
                "message": "Navigation successful."
            }
        except Exception as e:
            if "timeout" in str(e).lower():
                # Timeout is not a crash, the page might still have loaded mostly
                return {
                    "success": False,
                    "error": "Navigation timed out waiting for page load, but browser session remains available.",
                    "recoverable": True,
                    "url": page.url
                }
            raise e
            
    except Exception as e:
        logger.error(f"Navigation failed: {e}")
        return {"success": False, "error": f"Failed to navigate to {final_url}: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def go_back() -> dict:
    """Navigate back to the previous page."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed or unavailable."}
            
        try:
            # Playwright go_back returns null if there is no history
            res = page.go_back(wait_until="domcontentloaded", timeout=5000)
            if res is None:
                return {
                    "success": False,
                    "action": "go_back",
                    "error": "No previous page is available in history."
                }
        except Exception as e:
            if "Timeout" in str(e) or "timeout" in str(e).lower():
                return {
                    "success": False,
                    "action": "go_back",
                    "error": "Back navigation timed out, but the browser session remains available.",
                    "recoverable": True,
                    "url": page.url
                }
            raise e
                
        return {
            "success": True,
            "action": "go_back",
            "url": page.url,
            "title": page.title(),
            "message": "Navigated back successfully."
        }
    except Exception as e:
        return {"success": False, "action": "go_back", "error": f"Failed to go back: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def go_forward() -> dict:
    """Navigate forward to the next page."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        try:
            res = page.go_forward(wait_until="domcontentloaded", timeout=5000)
            if res is None:
                return {"success": False, "error": "No forward page is available."}
        except Exception as e:
            if "timeout" in str(e).lower():
                return {"success": False, "error": "Forward navigation timed out, but is recoverable.", "recoverable": True}
            raise e
            
        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
            "message": "Went forward successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to go forward: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def refresh_page() -> dict:
    """Refresh the current page."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        try:
            page.reload(wait_until="domcontentloaded", timeout=5000)
        except Exception as e:
            if "timeout" in str(e).lower():
                return {"success": False, "error": "Refresh timed out, but is recoverable.", "recoverable": True}
            raise e
            
        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
            "message": "Refreshed successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to refresh: {str(e)}"}
