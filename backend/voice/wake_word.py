"""
Stage 5: WakeWordDetector — records a short clip with the system default
microphone and fuzzy-matches against the wake phrase via Google STT.
No amplitude filtering, no Bluetooth logic.
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

    def detect(self) -> bool:
        if not self._running:
            return False
        try:
            import numpy as np
            import sounddevice as sd
            import io, wave, speech_recognition as sr

            RATE = 16000
            DURATION = 1.5

            audio_array = sd.rec(int(DURATION * RATE),
                                 samplerate=RATE, channels=1,
                                 dtype="int16", blocking=True)

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
                return False
            except sr.RequestError as exc:
                logger.warning(f"[VOICE] STT error: {exc}")
                time.sleep(1.0)
                return False

        except Exception as exc:
            logger.warning(f"[VOICE] detect() error: {exc}")
            time.sleep(0.2)
            return False

    def _is_wake_phrase(self, text: str) -> bool:
        wake_words = set(self._wake_phrase.split())
        heard_words = set(text.split())
        if "jarvis" not in heard_words:
            return False
        score = len(wake_words & heard_words) / len(wake_words) if wake_words else 0
        matched = score >= 0.5
        if matched:
            logger.info(f"[VOICE] Wake word detected! (heard=\"{text}\")")
        return matched


def create_wake_word_detector(stt) -> BaseWakeWordDetector:
    return FuzzyWakeWordDetector(stt)

