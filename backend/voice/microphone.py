"""
Stage 5: VoiceInput — microphone abstraction layer.

Wraps the SpeechRecognition library with graceful error handling so that
microphone unavailability NEVER crashes the main JARVIS process.
"""
import logging
from typing import Optional

logger = logging.getLogger("backend.voice.microphone")

# Soft import — the entire voice module is optional
try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False
    logger.warning("[VOICE] SpeechRecognition library not installed. Voice input unavailable.")


class VoiceInput:
    """Abstraction over microphone access."""

    def __init__(self):
        self._recognizer: Optional[object] = None
        self._microphone: Optional[object] = None
        self._running = False

    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        """Return True if a microphone is accessible."""
        if not _SR_AVAILABLE:
            return False
        try:
            mic_names = sr.Microphone.list_microphone_names()
            return len(mic_names) > 0
        except Exception as exc:
            logger.warning(f"[VOICE] Microphone check failed: {exc}")
            return False

    # ------------------------------------------------------------------
    def start(self) -> bool:
        """
        Initialise recogniser and microphone.
        Returns True on success, False if unavailable.
        """
        if not self.is_available():
            logger.warning("[VOICE] Microphone unavailable — voice input disabled.")
            return False
        try:
            self._recognizer = sr.Recognizer()
            self._recognizer.dynamic_energy_threshold = True
            self._microphone = sr.Microphone()
            # Calibrate to ambient noise
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self._running = True
            logger.info("[VOICE] Microphone initialised successfully.")
            return True
        except OSError as exc:
            logger.error(f"[VOICE] Microphone permission/access error: {exc}")
            return False
        except Exception as exc:
            logger.error(f"[VOICE] Failed to start microphone: {exc}")
            return False

    # ------------------------------------------------------------------
    def stop(self):
        """Release microphone resources."""
        self._running = False
        self._microphone = None
        self._recognizer = None
        logger.info("[VOICE] Microphone stopped.")

    # ------------------------------------------------------------------
    def listen(self, timeout: float = 5.0, phrase_time_limit: float = 10.0) -> Optional[object]:
        """
        Capture audio from the microphone.

        Returns an AudioData object on success, or None on failure/timeout.
        """
        if not self._running or self._recognizer is None or self._microphone is None:
            logger.warning("[VOICE] listen() called but microphone is not started.")
            return None
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            return audio
        except sr.WaitTimeoutError:
            logger.debug("[VOICE] listen() timed out — no speech detected.")
            return None
        except Exception as exc:
            logger.warning(f"[VOICE] listen() error: {exc}")
            return None

    # ------------------------------------------------------------------
    @property
    def recognizer(self):
        return self._recognizer
