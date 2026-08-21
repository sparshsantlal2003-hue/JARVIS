import time
from typing import Optional, Dict, List, Any
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright
from backend.logger import setup_logger
import uuid

logger = setup_logger(__name__)

class BrowserManager:
    """Manages a persistent Playwright browser session with stable tab tracking."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.current_page: Optional[Page] = None
        
        # stable tab id mapping: tab_id -> Page
        self.tab_registry: Dict[str, Page] = {}
        
        self._initialized = True
        logger.info("BrowserManager initialized (lazy).")

    def sync_tabs(self):
        """Sweep the browser contexts and rebuild the tab registry, culling dead pages."""
        if not self.browser:
            return
            
        # Get all currently open Playwright pages across all contexts
        actual_pages = []
        try:
            for ctx in self.browser.contexts:
                actual_pages.extend(ctx.pages)
        except Exception as e:
            logger.warning(f"Failed to fetch pages during sync: {e}")
            return
            
        # Remove dead/closed pages from our registry
        dead_keys = []
        for tab_id, page in self.tab_registry.items():
            if page.is_closed() or page not in actual_pages:
                dead_keys.append(tab_id)
        for k in dead_keys:
            del self.tab_registry[k]
            
        # Add new pages to registry
        registered_pages = list(self.tab_registry.values())
        for page in actual_pages:
            if page not in registered_pages and not page.is_closed():
                # Assign a stable identifier
                new_id = f"tab_{str(uuid.uuid4())[:8]}"
                self.tab_registry[new_id] = page
                
        # Ensure current_page is still valid
        if self.current_page and (self.current_page.is_closed() or self.current_page not in actual_pages):
            self.current_page = None
            
        # Fallback to the last available page if current is None
        if not self.current_page and self.tab_registry:
            self.current_page = list(self.tab_registry.values())[-1]
            
        # Apply dark mode globally to prevent light bleed
        try:
            for p in self.tab_registry.values():
                p.emulate_media(color_scheme="dark")
        except Exception:
            pass

    def ensure_browser_running(self) -> Page:
        """Ensure the browser is running and return the active page."""
        try:
            if self.playwright is None:
                logger.info("Starting Playwright...")
                self.playwright = sync_playwright().start()
                
            if self.browser is None or not self.browser.is_connected():
                logger.info("Connecting to active Brave browser via CDP on port 9222...")
                self.browser = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
                self.context = None
                self.tab_registry.clear()
                    
            if self.context is None:
                if self.browser.contexts:
                    self.context = self.browser.contexts[0]
                else:
                    self.context = self.browser.new_context()

                # Intercept popup/new-window events and redirect into the current tab
                # instead of opening a new window. This prevents YouTube etc. from
                # hijacking focus by spawning new browser windows.
                def _handle_popup(popup):
                    try:
                        popup_url = popup.url
                        logger.info(f"Popup intercepted: {popup_url} — redirecting to active tab.")
                        popup.close()
                        if self.current_page and not self.current_page.is_closed():
                            self.current_page.goto(popup_url, wait_until="domcontentloaded", timeout=10000)
                            self.current_page.bring_to_front()
                    except Exception as pe:
                        logger.warning(f"Popup handler error: {pe}")

                self.context.on("page", _handle_popup)
                    
            self.sync_tabs()
            
            if self.current_page is None:
                logger.info("Creating new page in existing Brave session...")
                new_page = self.context.new_page()
                self.sync_tabs()
                self.current_page = new_page
                
            return self.current_page
            
        except Exception as e:
            error_msg = f"Browser connection error (EPIPE or disconnected). Make sure Brave is running with --remote-debugging-port=9222. Details: {e}"
            logger.error(error_msg)
            # Try to safely shut down existing dead pipes
            try:
                self.close()
            except:
                pass
            raise RuntimeError(error_msg)

    def get_active_page(self) -> Page:
        """Get the current active page, ensuring browser is running."""
        return self.ensure_browser_running()
        
    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get structured list of synchronized tabs."""
        self.ensure_browser_running()
        self.sync_tabs()
        
        tabs_list = []
        # Sort them generally by creation order implicitly provided by dict items
        for idx, (tab_id, page) in enumerate(self.tab_registry.items()):
            try:
                tabs_list.append({
                    "tab_id": tab_id,
                    "index": idx,
                    "title": page.title() if not page.is_closed() else "Closed",
                    "url": page.url if not page.is_closed() else "",
                    "active": (page == self.current_page)
                })
            except Exception:
                pass
        return tabs_list
        
    def get_page_by_id(self, tab_id: str) -> Optional[Page]:
        self.sync_tabs()
        return self.tab_registry.get(tab_id)
        
    def close(self):
        """Cleanly close the browser session."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
        finally:
            self.context = None
            self.browser = None
            self.playwright = None
            self.current_page = None
            self.tab_registry.clear()
            logger.info("Browser session closed.")

# Global singleton
browser_manager = BrowserManager()

