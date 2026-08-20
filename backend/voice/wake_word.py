"""
Stage 5: WakeWordDetector — lightweight, pluggable wake-word detection.

Uses the smart MicrophoneSelector to automatically use Bluetooth earbuds
when connected, or fall back to the system microphone when disconnected.
"""
import logging
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
            from backend.voice.mic_selector import get_best_device

            RATE = 16000
            DURATION = 1.2  # seconds — tight window for fast wake-word response

            # Auto-select best mic (BT earbuds or system mic)
            device_index, device_name = get_best_device()
            logger.debug(f"[VOICE] Wake word mic: [{device_index}] {device_name}")

            rec_kwargs = dict(
                samplerate=RATE,
                channels=1,
                dtype="int16",
                blocking=True
            )
            if device_index is not None:
                rec_kwargs["device"] = device_index

            audio_array = sd.rec(int(DURATION * RATE), **rec_kwargs)

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
            logger.debug(f"[VOICE] Wake-word clip: \"{text}\"")
            return self._is_wake_phrase(text)

        except Exception as exc:
            logger.debug(f"[VOICE] Wake-word detect() skipped: {exc}")
            return False

    def _is_wake_phrase(self, text: str) -> bool:
        wake_words = set(self._wake_phrase.split())
        heard_words = set(text.split())
        if "jarvis" not in heard_words:
            return False
        match_count = len(wake_words & heard_words)
        score = match_count / len(wake_words) if wake_words else 0
        matched = score >= 0.5
        if matched:
            logger.info(f"[VOICE] Wake word detected! (score={score:.2f}, text=\"{text}\")")
        return matched


def create_wake_word_detector(stt) -> BaseWakeWordDetector:
    return FuzzyWakeWordDetector(stt)
