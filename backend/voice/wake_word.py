"""
Stage 5: WakeWordDetector — two-phase (local VAD + Google STT).
Uses WASAPI 48kHz → downsample for reliable Windows microphone support.
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
    SPEECH_THRESHOLD = 150  # tuned for WASAPI (amp peaks ~500-2000 when speaking)

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
            from backend.voice.stt import _downsample, TARGET_RATE

            device_index, device_name, native_rate = get_best_device()
            channels = 2 if native_rate == 48000 else 1
            DURATION = 1.5
            n_samples = int(native_rate * DURATION)

            rec_kwargs = dict(samplerate=native_rate, channels=channels, dtype="int16", blocking=True)
            if device_index is not None:
                rec_kwargs["device"] = device_index

            audio_array = sd.rec(n_samples, **rec_kwargs)

            # Phase 1: local VAD
            amplitude = float(np.abs(audio_array).mean())
            if amplitude < self.SPEECH_THRESHOLD:
                time.sleep(0.05)
                return False

            logger.debug(f"[VOICE] Speech detected (amp={amplitude:.0f}), checking wake phrase...")

            # Phase 2: downsample → STT
            mono = _downsample(audio_array, native_rate, TARGET_RATE)
            pcm = mono.astype("int16").tobytes()

            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(TARGET_RATE)
                wf.writeframes(pcm)
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
                logger.warning(f"[VOICE] STT request error: {exc}")
                time.sleep(1.0)
                return False

        except Exception as exc:
            logger.debug(f"[VOICE] detect() error: {exc}")
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
            logger.info(f"[VOICE] Wake word detected! (score={score:.2f}, heard=\"{text}\")")
        return matched


def create_wake_word_detector(stt) -> BaseWakeWordDetector:
    return FuzzyWakeWordDetector(stt)
