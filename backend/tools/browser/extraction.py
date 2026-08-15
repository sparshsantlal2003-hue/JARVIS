from backend.logger import setup_logger
from backend.tools.registry import registry
from backend.tools.browser.browser_manager import browser_manager
import json

logger = setup_logger(__name__)

@registry.register(requires_confirmation=False, risk_level="LOW")
def read_page() -> dict:
    """Extract visible text and headings from the current page."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
        
        # Simple extraction using JS to avoid large token counts
        extraction_script = """
        () => {
            let text = document.body.innerText || "";
            return text.substring(0, 1500); // Strict limit to prevent TPM bloat
        }
        """
        content = page.evaluate(extraction_script)
        
        headings = page.evaluate("""
        () => {
            return Array.from(document.querySelectorAll('h1, h2, h3'))
                .map(h => ({tag: h.tagName, text: h.innerText.trim()}))
                .filter(h => h.text.length > 0)
                .slice(0, 10); // Limit to top 10 headings
        }
        """)
        
        return {
            "success": True,
            "url": page.url,
            "title": page.title(),
            "headings": headings,
            "content": content
        }
    except Exception as e:
        logger.error(f"Failed to read page: {e}")
        return {"success": False, "error": f"Failed to read page: {str(e)}"}

@registry.register(requires_confirmation=False, risk_level="LOW")
def extract_links() -> dict:
    """Extract visible links from the current page."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
        
        links = page.evaluate("""
        () => {
            return Array.from(document.querySelectorAll('a[href]'))
                .filter(a => a.innerText.trim().length > 0)
                .map((a, i) => ({
                    text: a.innerText.trim().substring(0, 50),
                    href: a.href
                }))
                .slice(0, 15); // Strict limit to 15 links
        }
        """)
        
        return {
            "success": True,
            "url": page.url,
            "links": links,
            "message": f"Found {len(links)} links."
        }
    except Exception as e:
        logger.error(f"Failed to extract links: {e}")
        return {"success": False, "error": f"Failed to extract links: {str(e)}"}
