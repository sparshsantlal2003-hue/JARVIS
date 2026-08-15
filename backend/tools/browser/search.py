from urllib.parse import quote_plus
from backend.logger import setup_logger
from backend.tools.registry import registry
from backend.tools.browser.browser_manager import browser_manager
import time

logger = setup_logger(__name__)

@registry.register(requires_confirmation=False, risk_level="LOW")
def search_web(query: str) -> dict:
    """Search the web using Google and return top results."""
    try:
        page = browser_manager.get_active_page()
        if not page or page.is_closed():
            return {"success": False, "error": "Browser page is closed."}
            
        search_url = f"https://www.google.com/search?q={quote_plus(query)}"
        logger.info(f"Searching web for: {query}")
        
        page.goto(search_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(2) # Give dynamic search results a moment to render
        
        results = []
        
        # Try standard div.g first
        elements = page.query_selector_all("div.g")
        for el in elements:
            title_el = el.query_selector("h3")
            url_el = el.query_selector("a")
            if title_el and url_el:
                url = url_el.get_attribute("href")
                if url and url.startswith("http"):
                    results.append({
                        "position": len(results) + 1,
                        "title": title_el.inner_text().strip(),
                        "url": url,
                        "snippet": el.inner_text().replace(title_el.inner_text(), "").strip()[:200]
                    })
            if len(results) >= 5:
                break
                
        # If div.g fails (Google DOM changed), fallback to robust a:has(h3)
        if len(results) == 0:
            try:
                elements = page.locator("a:has(h3)").all()
                for el in elements:
                    try:
                        title = el.locator("h3").first.inner_text().strip()
                        url = el.get_attribute("href")
                        if title and url and url.startswith("http") and "google.com" not in url:
                            results.append({
                                "position": len(results) + 1,
                                "title": title,
                                "url": url,
                                "snippet": "Result extracted via robust selector."
                            })
                    except Exception:
                        pass
                    if len(results) >= 5:
                        break
            except Exception as e:
                logger.warning(f"Fallback scraper also failed: {e}")
                
        # SUPER FALLBACK: If still 0 results, just grab the first 5 external links from the #search container
        if len(results) == 0:
            try:
                links = page.locator("#search a[href^='http']").all()
                for link in links:
                    url = link.get_attribute("href")
                    title = link.inner_text().strip()
                    if title and url and "google.com" not in url and len(title) > 3:
                        # Avoid duplicates
                        if not any(r["url"] == url for r in results):
                            results.append({
                                "position": len(results) + 1,
                                "title": title,
                                "url": url,
                                "snippet": "Extracted via super fallback."
                            })
                    if len(results) >= 5:
                        break
            except Exception:
                pass
                
        # ULTIMATE FALLBACK: Just grab any external links on the whole page
        if len(results) == 0:
            try:
                links = page.locator("a[href^='http']").all()
                for link in links:
                    url = link.get_attribute("href")
                    title = link.inner_text().strip()
                    if title and url and "google.com" not in url and len(title) > 3:
                        if not any(r["url"] == url for r in results):
                            results.append({
                                "position": len(results) + 1,
                                "title": title,
                                "url": url,
                                "snippet": "Extracted via ultimate fallback."
                            })
                    if len(results) >= 5:
                        break
            except Exception:
                pass

        if len(results) == 0:
            return {"success": False, "error": "No results could be extracted from the Google search page. The DOM might have changed significantly or a captcha might be blocking it."}
            
        return {
            "success": True,
            "query": query,
            "results": results,
            "message": f"Found {len(results)} results."
        }
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"success": False, "error": f"Failed to perform search: {str(e)}"}
