import pystray
from PIL import Image
import threading
import sys
import os
from pathlib import Path
from backend.shutdown import shutdown_manager

_tray_icon = None
_voice_loop = None

def on_pause_resume(icon, item):
    global _voice_loop
    if _voice_loop:
        _voice_loop.paused = not _voice_loop.paused
        # Update menu text dynamically based on state
        update_menu()

def on_restart(icon, item):
    print("\n[TRAY] Restart requested.")
    # Restart the current process
    # We use python executable instead of pythonw so we see the console if it was started via console.
    # Actually, in background mode, we shouldn't care. Let's just restart using the same arguments.
    import subprocess
    subprocess.Popen([sys.executable] + sys.argv)
    shutdown_manager.shutdown()

def on_shutdown(icon, item):
    print("\n[TRAY] Shutdown requested.")
    shutdown_manager.shutdown()

def update_menu():
    global _tray_icon, _voice_loop
    if not _tray_icon: return
    
    paused = getattr(_voice_loop, 'paused', False) if _voice_loop else False
    status_text = "Status: Paused" if paused else "Status: Running"
    toggle_text = "Resume Listening" if paused else "Pause Listening"
    
    menu = pystray.Menu(
        pystray.MenuItem('JARVIS Assistant', None, enabled=False),
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(toggle_text, on_pause_resume),
        pystray.MenuItem('Restart JARVIS', on_restart),
        pystray.MenuItem('Shutdown JARVIS', on_shutdown)
    )
    _tray_icon.menu = menu

def _run_tray():
    global _tray_icon
    icon_path = Path(__file__).parent.parent / 'assets' / 'jarvis.ico'
    try:
        image = Image.open(icon_path)
    except FileNotFoundError:
        # Fallback to creating a simple image if icon is missing
        image = Image.new('RGB', (64, 64), color=(0, 255, 255))
    
    _tray_icon = pystray.Icon("JARVIS", image, "JARVIS Background Assistant")
    update_menu()
    
    # This runs the tray event loop in this thread
    _tray_icon.run()

def start_tray(voice_loop=None):
    """Starts the system tray icon in a daemon thread."""
    global _voice_loop
    _voice_loop = voice_loop
    tray_thread = threading.Thread(target=_run_tray, daemon=True)
    tray_thread.start()
    return tray_thread

def stop_tray():
    global _tray_icon
    if _tray_icon:
        _tray_icon.stop()
