"""
ShutdownManager — deterministic, LLM-bypass shutdown for JARVIS.

Responsibilities:
  - Detect shutdown intent from raw user text (text or transcribed voice).
  - Provide a thread-safe event flag so any part of the system can request shutdown.
  - Execute orderly cleanup: voice resources → browser → process exit.

SECURITY: Only trusted user input should be passed to is_shutdown_command().
Do NOT pass webpage content, tool output, or LLM responses here.
"""
import logging
import re
import sys
import threading

logger = logging.getLogger("backend.shutdown")

# ─── Shutdown phrase patterns (matched before LLM call) ───────────────────────
# These are exact-intent phrases. "What command closes JARVIS?" will NOT match.
_SHUTDOWN_PATTERNS = [
    # Single-word commands
    r"^exit$",
    r"^quit$",
    r"^shutdown$",
    r"^bye$",
    # Two-word with JARVIS
    r"^close\s+jarvis$",
    r"^stop\s+jarvis$",
    r"^exit\s+jarvis$",
    r"^quit\s+jarvis$",
    r"^goodbye\s+jarvis$",
    r"^terminate\s+jarvis$",
    r"^shutdown\s+jarvis$",
    # Self-referential voice variants
    r"^shut\s+(yourself|itself)\s+down$",
    r"^close\s+yourself(\s+down)?$",
    r"^stop\s+yourself(\s+down)?$",
    r"^turn\s+yourself\s+off$",
    r"^shut\s+down$",
    r"^power\s+off$",
    r"^goodbye$",
    # "Shut down JARVIS [now/please]"
    r"^shut\s+down\s+jarvis(\s+(now|please))?$",
    r"^close\s+jarvis(\s+(now|please))?$",
    r"^stop\s+jarvis(\s+(now|please))?$",
    r"^exit\s+jarvis(\s+(now|please))?$",
    r"^terminate\s+jarvis(\s+(now|please))?$",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _SHUTDOWN_PATTERNS]

FAREWELL_MESSAGE = "Shutting down. Goodbye."


def is_shutdown_command(text: str) -> bool:
    """
    Deterministic check — returns True only for explicit shutdown commands.
    Safe to call with raw user input; never passes to LLM.
    """
    normalized = text.strip().lower()
    for pattern in _COMPILED:
        if pattern.match(normalized):
            return True
    return False


class ShutdownManager:
    """
    Thread-safe shutdown lifecycle manager.

    Usage:
        sm = ShutdownManager()
        sm.request_shutdown()      # request from anywhere
        sm.is_shutdown_requested() # poll from loop
        sm.shutdown(tts, wake_detector)  # full orderly cleanup + sys.exit
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._event = threading.Event()
        return cls._instance

    def request_shutdown(self):
        """Signal that shutdown has been requested (idempotent)."""
        if not self._event.is_set():
            logger.info("[SHUTDOWN] Shutdown requested.")
            self._event.set()

    def is_shutdown_requested(self) -> bool:
        return self._event.is_set()

    def reset(self):
        """Reset for testing purposes only."""
        self._event.clear()

    def shutdown(self, tts=None, wake_detector=None, speak_farewell: bool = True):
        """
        Perform orderly cleanup and terminate the process.

        Safe to call multiple times — cleanup is idempotent.

        Args:
            tts: TextToSpeech instance (optional).
            wake_detector: WakeWordDetector instance (optional).
            speak_farewell: Whether to speak the farewell via TTS.
        """
        self.request_shutdown()

        logger.info("[SHUTDOWN] Starting cleanup sequence.")

        # 1. Farewell message
        print(f"\nJARVIS: {FAREWELL_MESSAGE}", flush=True)

        # 2. Speak farewell if TTS available and requested
        if speak_farewell and tts is not None:
            try:
                tts.speak_and_wait(FAREWELL_MESSAGE)
            except Exception as exc:
                logger.warning(f"[SHUTDOWN] TTS farewell failed: {exc}")

        # 3. Stop wake word detector / audio stream
        if wake_detector is not None:
            logger.info("[SHUTDOWN] Stopping voice system.")
            try:
                wake_detector.stop()
            except Exception as exc:
                logger.warning(f"[SHUTDOWN] Wake detector stop failed: {exc}")

        # 4. Stop TTS engine
        if tts is not None:
            logger.info("[SHUTDOWN] Stopping TTS.")
            try:
                tts.stop()
            except Exception as exc:
                logger.warning(f"[SHUTDOWN] TTS stop failed: {exc}")

        # 5. Release browser resources JARVIS owns (Playwright session)
        try:
            from backend.tools.browser.browser_manager import browser_manager
            if browser_manager.browser and browser_manager.browser.is_connected():
                logger.info("[SHUTDOWN] Releasing browser resources.")
                browser_manager.close()
        except Exception as exc:
            logger.warning(f"[SHUTDOWN] Browser cleanup failed (safe to ignore): {exc}")

        logger.info("[SHUTDOWN] Cleanup complete.")
        logger.info("[SHUTDOWN] JARVIS terminated.")

        sys.exit(0)


# Module-level singleton
shutdown_manager = ShutdownManager()
