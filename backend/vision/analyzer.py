from typing import Optional, Dict, Any, Tuple
from backend.logger import setup_logger
from backend.config import settings
from backend.vision.capture import capture
from backend.vision.window import window_detector
from backend.vision.provider import vision_provider

logger = setup_logger(__name__)

class ScreenAnalyzer:
    """Orchestrates screen capture, active window detection, and AI vision analysis."""
    
    def _capture_active_context(self):
        """Captures the screen and gets the active window info."""
        active_win = window_detector.get_active_window()
        # If we have an active window, we could capture just its bounds to save tokens
        # but the prompt implies full screen or active monitor is generally expected for context.
        # Let's capture the active monitor's bounding box. For now, capture_screen handles it.
        # Passing bbox based on active window could clip important context if the window is small.
        # Capture strictly the active window to improve model coordinate accuracy
        bbox = None
        if active_win:
            # bbox is (left, top, right, bottom)
            bbox = (active_win['left'], active_win['top'], active_win['right'], active_win['bottom'])
        
        image = capture.capture_screen(bbox=bbox)
        return image, active_win
        
    def describe_screen(self) -> str:
        """Returns a natural language description of the current screen."""
        if not getattr(settings, 'vision_enabled', False):
            return "Vision is currently disabled in settings."
            
        try:
            image, active_win = self._capture_active_context()
            
            context_str = ""
            if active_win:
                context_str = f" The active window is '{active_win['title']}'."
                
            query = f"Describe the visible UI elements and overall state of the screen.{context_str}"
            description = vision_provider.analyze_screen(image, query)
            
            # Privacy: ensure temp capture is deleted
            capture.cleanup()
            return description
            
        except Exception as e:
            logger.error(f"Failed to describe screen: {e}")
            return f"Error analyzing screen: {e}"
            
    def verify_state(self, expected_state: str) -> bool:
        """Verifies if the expected state is true based on the current screen."""
        if not getattr(settings, 'vision_enabled', False):
            return False
            
        try:
            image, active_win = self._capture_active_context()
            query = f"Is the following statement true about this screen: '{expected_state}'? Reply only with 'yes' or 'no'."
            result = vision_provider.analyze_screen(image, query)
            capture.cleanup()
            
            if "yes" in result.lower():
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify state: {e}")
            return False

    def locate_element(self, target: str) -> Optional[Dict[str, Any]]:
        """Locates an element on screen and verifies confidence."""
        if not getattr(settings, 'vision_enabled', False):
            logger.warning("Vision is disabled, cannot locate element.")
            return None
            
        try:
            image, active_win = self._capture_active_context()
            
            data = vision_provider.locate_element(image, target)
            capture.cleanup()
            
            if not data:
                logger.warning(f"Element '{target}' not found on screen.")
                return None
                
            min_confidence = getattr(settings, 'vision_min_confidence', 0.80)
            if data.get('confidence', 0) < min_confidence:
                logger.warning(f"Found '{target}' but confidence ({data['confidence']}) is below threshold ({min_confidence}).")
                return None
                
            # If the image was a full screen capture, the x,y returned by the model
            # are relative to the top-left of the image.
            # We must map these coordinates back to the global screen if necessary, 
            # but since we captured the primary screen (which starts at 0,0), they are absolute.
            
            # Translate coordinates back to global absolute screen space
            abs_x = data['x']
            abs_y = data['y']
            
            if active_win:
                abs_x += active_win['left']
                abs_y += active_win['top']
                
            return {
                "x": abs_x,
                "y": abs_y,
                "confidence": data['confidence'],
                "target": target,
                "active_window": active_win['title'] if active_win else "Unknown"
            }
            
        except Exception as e:
            logger.error(f"Failed to locate element '{target}': {e}")
            return None

analyzer = ScreenAnalyzer()
