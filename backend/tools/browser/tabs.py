from backend.logger import setup_logger
from backend.tools.registry import registry
from backend.tools.browser.browser_manager import browser_manager

logger = setup_logger(__name__)

@registry.register(requires_confirmation=False, risk_level="LOW")
def list_tabs() -> dict:
    """List all open browser tabs and their stable tab_ids."""
    try:
        tabs = browser_manager.get_tabs()
        if not tabs:
            return {"success": True, "tabs": [], "message": "No browser tabs are currently open."}
        return {"success": True, "tabs": tabs}
    except Exception as e:
        return {"success": False, "error": f"Failed to list tabs: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def open_new_tab(url: str = "about:blank") -> dict:
    """Open a new browser tab and switch to it."""
    try:
        page = browser_manager.get_active_page()
        # To strictly open a new one rather than returning existing:
        if browser_manager.context:
            new_page = browser_manager.context.new_page()
            browser_manager.sync_tabs()
            browser_manager.current_page = new_page
            
        if url != "about:blank":
            from backend.tools.browser.navigation import navigate
            return navigate(url)
            
        return {"success": True, "message": "Opened new blank tab."}
    except Exception as e:
        return {"success": False, "error": f"Failed to open new tab: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def switch_tab(target: str) -> dict:
    """Switch to a specific tab using its tab_id or list index (e.g., '0' for first tab)."""
    try:
        tabs = browser_manager.get_tabs()
        if not tabs:
            return {"success": False, "error": "No browser tabs are currently available."}
            
        target_page = None
        
        # Check if target is a tab_id
        target_page = browser_manager.get_page_by_id(target)
        
        # If not, check if it's an index
        if target_page is None:
            try:
                idx = int(target)
                if 0 <= idx < len(tabs):
                    target_id = tabs[idx]["tab_id"]
                    target_page = browser_manager.get_page_by_id(target_id)
            except ValueError:
                pass
                
        if target_page is None:
            return {
                "success": False, 
                "error": f"Tab '{target}' no longer exists or is invalid.",
                "available_tabs": [t['tab_id'] for t in tabs]
            }
            
        browser_manager.current_page = target_page
        target_page.bring_to_front()
        
        return {
            "success": True, 
            "target": target,
            "title": target_page.title(),
            "message": f"Switched to tab successfully."
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to switch tab: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def close_tab(target: str) -> dict:
    """Close a specific tab using its tab_id or index."""
    try:
        tabs = browser_manager.get_tabs()
        if not tabs:
            return {"success": False, "error": "No tabs available to close."}
            
        target_page = browser_manager.get_page_by_id(target)
        if target_page is None:
            try:
                idx = int(target)
                if 0 <= idx < len(tabs):
                    target_id = tabs[idx]["tab_id"]
                    target_page = browser_manager.get_page_by_id(target_id)
            except ValueError:
                pass
                
        if target_page is None:
            return {"success": False, "error": f"Tab '{target}' not found."}
            
        target_page.close()
        browser_manager.sync_tabs()
        
        return {"success": True, "message": f"Closed tab '{target}'."}
    except Exception as e:
        return {"success": False, "error": f"Failed to close tab: {str(e)}"}
