"""
Stage 5: WakeWordDetector — lightweight, pluggable wake-word detection.

Strategy: Two-phase passive listen.
  1. Record a short 2.5s audio clip (very short, low cost).
  2. Transcribe it with Google STT.
  3. Fuzzy-match the transcription against the configured wake phrase.

This avoids binary ML model dependencies while remaining modular —
a Porcupine or Vosk adapter can be dropped in later by subclassing BaseWakeWordDetector.
"""
import logging
import threading
from typing import Optional
from backend.config import settings

logger = logging.getLogger("backend.voice.wake_word")


class BaseWakeWordDetector:
    """Abstract interface. Subclass to implement alternative engines."""
    def start(self): ...
    def stop(self): ...
    def detect(self) -> bool: ...
    def is_running(self) -> bool: ...


class FuzzyWakeWordDetector(BaseWakeWordDetector):
    """
    Default implementation: short STT clip + fuzzy phrase match.
    Lightweight, no external API keys required.
    """

    def __init__(self, stt, wake_phrase: Optional[str] = None):
        """
        Args:
            stt: SpeechRecognizer instance (already initialised).
            wake_phrase: The phrase to listen for (e.g. "hello jarvis").
        """
        self._stt = stt
        self._wake_phrase = (wake_phrase or settings.wake_word).lower().strip()
        self._running = False
        logger.info(f"[VOICE] Wake phrase: \"{self._wake_phrase}\"")

    # ------------------------------------------------------------------
    def start(self):
        self._running = True
        logger.debug("[VOICE] WakeWordDetector started.")

    def stop(self):
        self._running = False
        logger.debug("[VOICE] WakeWordDetector stopped.")

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    def detect(self) -> bool:
        """
        Listen for a short clip and return True if the wake phrase is heard.

        Returns False on timeout, STT failure, or no match.
        """
        if not self._running:
            return False

        # Record a very short clip just for wake-word detection
        try:
            import numpy as np
            import sounddevice as sd
            import io, wave, speech_recognition as sr

            RATE = 16000
            DURATION = 2.5  # seconds — short enough to be responsive

            audio_array = sd.rec(
                int(DURATION * RATE),
                samplerate=RATE,
                channels=1,
                dtype="int16",
                blocking=True
            )

            # Convert to SR AudioData
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(RATE)
                wf.writeframes(audio_array.tobytes())
            buf.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(buf) as source:
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio).lower().strip()
            logger.debug(f"[VOICE] Wake-word clip heard: \"{text}\"")

            return self._is_wake_phrase(text)

        except Exception as exc:
            logger.debug(f"[VOICE] Wake-word detect() skipped: {exc}")
            return False

    # ------------------------------------------------------------------
    def _is_wake_phrase(self, text: str) -> bool:
        """
        Fuzzy match: the wake phrase words must all appear in the heard text.
        Tolerates minor transcription errors (e.g. "hey jarvis" vs "hello jarvis").
        """
        wake_words = set(self._wake_phrase.split())
        heard_words = set(text.split())

        # Must contain "jarvis" at minimum
        if "jarvis" not in heard_words:
            return False

        # Score: fraction of wake words found in heard text
        match_count = len(wake_words & heard_words)
        score = match_count / len(wake_words) if wake_words else 0
        matched = score >= 0.5  # At least 50% of wake phrase words detected
        if matched:
            logger.info(f"[VOICE] Wake word detected! (score={score:.2f}, text=\"{text}\")")
        return matched


def create_wake_word_detector(stt) -> BaseWakeWordDetector:
    """Factory: returns the best available detector."""
    return FuzzyWakeWordDetector(stt)
