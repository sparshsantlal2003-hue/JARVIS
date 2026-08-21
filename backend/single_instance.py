import ctypes
import sys
import logging

logger = logging.getLogger("backend.single_instance")

ERROR_ALREADY_EXISTS = 183
MUTEX_NAME = "Global\\JARVIS_BACKGROUND_MUTEX"

_mutex_handle = None

def enforce_single_instance():
    """
    Ensures that only one instance of JARVIS runs at a time using a named Windows Mutex.
    If another instance is detected, it logs a warning and exits the process cleanly.
    """
    global _mutex_handle
    kernel32 = ctypes.windll.kernel32
    
    _mutex_handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    
    last_error = kernel32.GetLastError()
    if last_error == ERROR_ALREADY_EXISTS:
        logger.warning("Another instance of JARVIS is already running. Exiting.")
        print("\n[JARVIS] Another instance is already running. Exiting.\n")
        sys.exit(0)
        
def release_single_instance():
    """Releases the mutex if we hold it."""
    global _mutex_handle
    if _mutex_handle:
        ctypes.windll.kernel32.ReleaseMutex(_mutex_handle)
        _mutex_handle = None
