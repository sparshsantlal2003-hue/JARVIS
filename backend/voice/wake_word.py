"""
Stage 5: WakeWordDetector — lightweight, two-phase wake word detection.

Phase 1: LOCAL amplitude VAD — record a clip and check if speech energy
         is above threshold. FAST, no network call needed.
Phase 2: Only if speech detected — send to Google STT and fuzzy-match
         against the wake phrase.

This avoids hammering the STT API on silence and prevents the busy-loop.
"""
import logging
import time
from typing import Optional
from backend.config import settings

logger = logging.getLogger("backend.voice.wake_word")


class BaseWakeWordDetector:
    def start(self): ...
    def stop(self): ...
    def detect(self) -> bool: ...
    def is_running(self) -> bool: ...


class FuzzyWakeWordDetector(BaseWakeWordDetector):

    # Amplitude threshold — audio below this is treated as silence.
    # Tune up if your mic is very sensitive; tune down if it misses quiet speech.
    SPEECH_THRESHOLD = 400

    def __init__(self, stt, wake_phrase: Optional[str] = None):
        self._stt = stt
        self._wake_phrase = (wake_phrase or settings.wake_word).lower().strip()
        self._running = False
        logger.info(f"[VOICE] Wake phrase: \"{self._wake_phrase}\"")

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def is_running(self) -> bool:
        return self._running

    # ------------------------------------------------------------------
    def detect(self) -> bool:
        """
        Two-phase detection:
          1. Record short clip + check amplitude locally (free, instant)
          2. Only if speech detected → call Google STT + fuzzy match

        Returns True if the wake phrase was heard, False otherwise.
        Sleeps briefly on silence so the terminal does not spam.
        """
        if not self._running:
            return False

        try:
            import numpy as np
            import sounddevice as sd
            import io, wave, speech_recognition as sr
            from backend.voice.mic_selector import get_best_device

            RATE = 16000
            DURATION = 1.5  # seconds per listen window

            device_index, device_name = get_best_device()

            rec_kwargs = dict(samplerate=RATE, channels=1, dtype="int16", blocking=True)
            if device_index is not None:
                rec_kwargs["device"] = device_index

            audio_array = sd.rec(int(DURATION * RATE), **rec_kwargs)

            # ── Phase 1: LOCAL VAD ────────────────────────────────────
            amplitude = float(np.abs(audio_array).mean())
            if amplitude < self.SPEECH_THRESHOLD:
                # Silence detected — sleep briefly then return False quietly
                # (no Google STT call, no log spam)
                time.sleep(0.05)
                return False

            # ── Phase 2: STT only when speech energy detected ─────────
            logger.debug(f"[VOICE] Speech energy detected (amp={amplitude:.0f}), checking for wake phrase...")

            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(RATE)
                wf.writeframes(audio_array.tobytes())
            buf.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(buf) as source:
                audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio_data).lower().strip()
                logger.debug(f"[VOICE] Heard: \"{text}\"")
                return self._is_wake_phrase(text)
            except sr.UnknownValueError:
                # Speech energy was there but unintelligible — not the wake phrase
                return False
            except sr.RequestError as exc:
                logger.warning(f"[VOICE] STT request failed: {exc}")
                time.sleep(1.0)  # Back off briefly on network error
                return False

        except Exception as exc:
            logger.debug(f"[VOICE] detect() error: {exc}")
            time.sleep(0.2)
            return False

    # ------------------------------------------------------------------
    def _is_wake_phrase(self, text: str) -> bool:
        """Fuzzy match — 'jarvis' must be present + ≥50% of wake words."""
        wake_words = set(self._wake_phrase.split())
        heard_words = set(text.split())
        if "jarvis" not in heard_words:
            return False
        score = len(wake_words & heard_words) / len(wake_words) if wake_words else 0
        matched = score >= 0.5
        if matched:
            logger.info(f"[VOICE] Wake word detected! (score={score:.2f}, heard=\"{text}\")")
        return matched


def create_wake_word_detector(stt) -> BaseWakeWordDetector:
    return FuzzyWakeWordDetector(stt)
