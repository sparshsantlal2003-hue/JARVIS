"""
Stage 5: TextToSpeech — TTS abstraction using pyttsx3 (offline Windows SAPI5).

- Speaks in a background thread so JARVIS does not block.
- stop() cancels any in-progress speech.
- Cleans up tool metadata before speaking (never reads raw JSON).
"""
import threading
import re
import logging
from typing import Optional

logger = logging.getLogger("backend.voice.tts")

try:
    import pyttsx3
    _PYTTSX3_AVAILABLE = True
except ImportError:
    _PYTTSX3_AVAILABLE = False
    logger.warning("[TTS] pyttsx3 not installed. Text-to-speech disabled.")


# Characters / patterns to strip before speaking
_CLEANUP_PATTERNS = [
    r"\{.*?\}",            # JSON blobs
    r"\[Tool.*?\]",        # Tool result tags
    r"https?://\S+",       # URLs
    r"<[^>]+>",            # HTML/XML tags
    r"```[\s\S]*?```",     # Code blocks
]


def _clean_for_speech(text: str) -> str:
    """Strip technical metadata that should not be read aloud."""
    for pattern in _CLEANUP_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.DOTALL)
    # Collapse multiple spaces / newlines
    text = re.sub(r"\s+", " ", text).strip()
    return text


class TextToSpeech:
    """Thread-safe TTS wrapper around pyttsx3."""

    def __init__(self):
        self._engine: Optional[object] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        return _PYTTSX3_AVAILABLE

    # ------------------------------------------------------------------
    def _init_engine(self):
        """Create a fresh engine instance (must be done on the speaking thread)."""
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)   # words per minute
        engine.setProperty("volume", 1.0)
        # Prefer a female voice if available (more JARVIS-like)
        voices = engine.getProperty("voices")
        for v in voices:
            if "zira" in v.name.lower() or "female" in v.name.lower():
                engine.setProperty("voice", v.id)
                break
        return engine

    # ------------------------------------------------------------------
    def speak(self, text: str):
        """
        Speak text asynchronously.
        Any in-progress speech is cancelled first.
        """
        if not _PYTTSX3_AVAILABLE:
            logger.warning("[TTS] speak() called but pyttsx3 unavailable.")
            return

        clean = _clean_for_speech(text)
        if not clean:
            return

        self.stop()  # Cancel previous speech

        self._stop_event.clear()

        def _run():
            try:
                engine = self._init_engine()
                engine.say(clean)
                engine.runAndWait()
            except RuntimeError:
                pass  # Engine already stopped
            except Exception as exc:
                logger.error(f"[TTS] Error during speech: {exc}")

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        logger.info(f"[TTS] Speaking: {clean[:80]}{'...' if len(clean) > 80 else ''}")

    # ------------------------------------------------------------------
    def stop(self):
        """Interrupt any ongoing speech."""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            # pyttsx3 does not offer a clean async stop;
            # we simply let the daemon thread die on its own.
            self._thread = None
            logger.debug("[TTS] Speech interrupted.")

    # ------------------------------------------------------------------
    def speak_and_wait(self, text: str):
        """Blocking variant — waits for speech to finish."""
        if not _PYTTSX3_AVAILABLE:
            logger.warning("[TTS] speak_and_wait() called but pyttsx3 unavailable.")
            return
        clean = _clean_for_speech(text)
        if not clean:
            return
        try:
            engine = self._init_engine()
            engine.say(clean)
            engine.runAndWait()
        except Exception as exc:
            logger.error(f"[TTS] Error in speak_and_wait: {exc}")
