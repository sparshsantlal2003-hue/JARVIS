import os
import tempfile
import uuid
from typing import Optional, Tuple
from PIL import Image, ImageGrab
from backend.logger import setup_logger

logger = setup_logger(__name__)

class ScreenCapture:
    """Handles screen capture functionality with privacy in mind."""
    
    def __init__(self):
        # We will use the system's temporary directory for temporary storage
        self.temp_dir = tempfile.gettempdir()
        self._last_capture_path: Optional[str] = None
        
    def capture_screen(self, bbox: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        Capture the screen or a specific bounding box.
        If bbox is provided, captures only that region (left, top, right, bottom).
        By default, ImageGrab.grab() grabs the primary monitor.
        If all_screens=True is passed, it grabs all monitors, but for token efficiency
        we typically just want the primary or a specific bbox.
        """
        logger.info(f"Capturing screen. BBox: {bbox}")
        try:
            # all_screens=True gets everything, but if bbox is provided we just pass it
            img = ImageGrab.grab(bbox=bbox, all_screens=True if not bbox else False)
            return img
        except Exception as e:
            logger.error(f"Failed to capture screen: {e}")
            raise

    def save_temp_capture(self, image: Image.Image) -> str:
        """
        Save the image to a temporary file and return its path.
        Automatically cleans up the previous temporary capture to protect privacy.
        """
        self.cleanup()
        
        filename = f"jarvis_vision_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(self.temp_dir, filename)
        
        try:
            image.save(filepath, "PNG")
            self._last_capture_path = filepath
            logger.debug(f"Saved temporary screenshot to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save temp capture: {e}")
            raise
            
    def cleanup(self):
        """Delete the last temporary capture from disk to ensure privacy."""
        if self._last_capture_path and os.path.exists(self._last_capture_path):
            try:
                os.remove(self._last_capture_path)
                logger.debug(f"Cleaned up temporary screenshot {self._last_capture_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp screenshot {self._last_capture_path}: {e}")
            finally:
                self._last_capture_path = None
                
    def get_screen_size(self) -> Tuple[int, int]:
        """Return the size of the primary screen."""
        img = ImageGrab.grab()
        return img.size

# Global singleton for basic usage
capture = ScreenCapture()
