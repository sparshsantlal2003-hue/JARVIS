import ctypes
from ctypes import wintypes
import time
from typing import Dict, Any, Optional
from backend.logger import setup_logger

logger = setup_logger(__name__)

# Windows API Types
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class RECT(ctypes.Structure):
    _fields_ = [
        ('left', wintypes.LONG),
        ('top', wintypes.LONG),
        ('right', wintypes.LONG),
        ('bottom', wintypes.LONG)
    ]

class ActiveWindowDetector:
    """Detects the foreground window and its bounds using Windows API."""
    
    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves information about the currently active foreground window.
        Returns a dict containing title, left, top, right, bottom, width, height.
        """
        try:
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None
                
            # Get Window Title
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value
            
            # Skip empty or irrelevant desktop windows
            if not title or title in ("Program Manager", "Task Switching"):
                return None
                
            # Get Window Rect
            rect = RECT()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return None
                
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            
            # Sometimes minimized or invisible windows return negative or zero dimensions
            if width <= 0 or height <= 0:
                return None
                
            return {
                "title": title,
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": width,
                "height": height
            }
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
            return None

window_detector = ActiveWindowDetector()
