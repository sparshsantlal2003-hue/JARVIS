from backend.logger import setup_logger
from backend.tools.registry import registry
from backend.vision.analyzer import analyzer
from backend.tools.mouse import click_mouse, move_mouse
from backend.config import settings

logger = setup_logger(__name__)

@registry.register(requires_confirmation=False, risk_level="LOW")
def describe_screen() -> dict:
    """
    Analyzes the current screen and active window visually.
    Returns a detailed natural language description of visible UI elements and text.
    Use this to understand what is currently on the user's screen.
    """
    logger.info("Executing describe_screen tool.")
    description = analyzer.describe_screen()
    return {
        "success": True,
        "description": description
    }

@registry.register(requires_confirmation=False, risk_level="LOW")
def visual_verify(expected_state: str) -> dict:
    """
    Takes a screenshot and visually verifies if the expected_state is true.
    Use this to confirm if an action (like opening a window) actually succeeded.
    Args:
        expected_state: A factual statement to verify (e.g. "The Settings window is open" or "The YouTube search bar is visible").
    """
    logger.info(f"Executing visual_verify tool for state: {expected_state}")
    result = analyzer.verify_state(expected_state)
    return {
        "success": True,
        "verified": result,
        "message": f"Visual verification for '{expected_state}' returned {result}."
    }

@registry.register(requires_confirmation=False, risk_level="MEDIUM")
def visual_click(target: str) -> dict:
    """
    Locates an element visually on the screen and clicks it.
    Use this ONLY as a fallback if deterministic tools (like launch_application, Playwright) fail or are unavailable.
    Args:
        target: The name, text, or description of the UI element to click (e.g. "Settings button" or "Search box").
    """
    logger.info(f"Executing visual_click tool for target: {target}")
    
    max_retries = getattr(settings, 'vision_max_retries', 2)
    
    for attempt in range(max_retries):
        element = analyzer.locate_element(target)
        if element:
            x, y = element['x'], element['y']
            confidence = element['confidence']
            logger.info(f"Visual click targeting '{target}' at ({x}, {y}) with confidence {confidence}")
            
            # Use existing mouse tools to move and click
            move_res = move_mouse(x, y)
            if not move_res.get("success"):
                return {"success": False, "error": f"Found element but failed to move mouse: {move_res.get('error')}"}
                
            click_res = click_mouse("left")
            if not click_res.get("success"):
                return {"success": False, "error": f"Found element but failed to click: {click_res.get('error')}"}
                
            return {
                "success": True,
                "action": "visual_click",
                "target": target,
                "confidence": confidence,
                "x": x,
                "y": y,
                "active_window": element.get("active_window")
            }
            
        logger.warning(f"Attempt {attempt+1}/{max_retries} to visually locate '{target}' failed.")
        
    return {
        "success": False,
        "error": f"Could not visually locate '{target}' with sufficient confidence after {max_retries} attempts."
    }
