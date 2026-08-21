"""
Stage 5: WakeWordDetector — continuous rolling-buffer listener.

Instead of fixed recording windows (which miss speech at window boundaries),
this streams audio continuously via a callback and checks the rolling buffer
every 0.5s for speech energy, then only calls Google STT when speech is detected.

This means the user can say "Hello JARVIS" at any moment and it will be captured.
"""
import io
import logging
import threading
import time
import wave
from collections import deque
from typing import Optional
from backend.config import settings

logger = logging.getLogger("backend.voice.wake_word")

RATE = 16000
CHUNK_MS = 50                       # 50ms chunks
CHUNK_SIZE = int(RATE * CHUNK_MS / 1000)
BUFFER_SECONDS = 4                  # keep last 4s in rolling buffer
BUFFER_CHUNKS = int(BUFFER_SECONDS * 1000 / CHUNK_MS)
SPEECH_THRESHOLD = 500              # amplitude to consider as speech
POLL_INTERVAL = 0.3                 # seconds between buffer checks


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
        self._stream = None
        self._buffer = deque(maxlen=BUFFER_CHUNKS)
        self._lock = threading.Lock()
        logger.info(f"[VOICE] Wake phrase: \"{self._wake_phrase}\"")

    def start(self):
        self._running = True
        self._start_stream()

    def _start_stream(self):
        """Start the continuous audio input stream."""
        try:
            import sounddevice as sd

            def _callback(indata, frames, time_info, status):
                with self._lock:
                    self._buffer.append(indata.copy().flatten())

            self._stream = sd.InputStream(
                samplerate=RATE,
                channels=1,
                dtype="int16",
                blocksize=CHUNK_SIZE,
                callback=_callback
            )
            self._stream.start()
            logger.info("[VOICE] Continuous audio stream started.")
        except Exception as exc:
            logger.error(f"[VOICE] Could not start audio stream: {exc}")
            self._stream = None

    def stop(self):
        self._running = False
        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        logger.info("[VOICE] Audio stream stopped.")

    def is_running(self) -> bool:
        return self._running

    def _get_buffer_audio(self, seconds: float = 2.5):
        """Get the last `seconds` worth of audio from the rolling buffer."""
        import numpy as np
        n_chunks = int(seconds * 1000 / CHUNK_MS)
        with self._lock:
            chunks = list(self._buffer)[-n_chunks:]
        if not chunks:
            return None
        return numpy_concat(chunks)

    def _has_speech(self, audio) -> bool:
        """Quick local check: is there enough energy in the audio?"""
        import numpy as np
        return float(np.abs(audio).max()) > SPEECH_THRESHOLD

    def detect(self) -> bool:
        """
        Poll the rolling buffer every POLL_INTERVAL seconds.
        If speech energy detected → send to STT → check for wake phrase.
        """
        if not self._running:
            return False

        if self._stream is None:
            # Stream failed to start — try to restart
            time.sleep(1.0)
            self._start_stream()
            return False

        time.sleep(POLL_INTERVAL)

        try:
            import numpy as np
            import speech_recognition as sr

            audio = self._get_buffer_audio(seconds=2.5)
            if audio is None or len(audio) == 0:
                return False

            # Fast local energy check before hitting the API
            if not self._has_speech(audio):
                return False

            logger.debug(f"[VOICE] Speech energy detected, checking wake phrase...")

            # Build WAV and send to Google STT
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(RATE)
                wf.writeframes(audio.astype("int16").tobytes())
            buf.seek(0)

            recognizer = sr.Recognizer()
            with sr.AudioFile(buf) as source:
                audio_data = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio_data).lower().strip()
                logger.debug(f"[VOICE] Heard: \"{text}\"")

                if self._is_wake_phrase(text):
                    # Clear buffer so we don't re-detect same phrase
                    with self._lock:
                        self._buffer.clear()
                    return True

            except sr.UnknownValueError:
                pass
            except sr.RequestError as exc:
                logger.warning(f"[VOICE] STT request error: {exc}")
                time.sleep(1.0)

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


def numpy_concat(chunks):
    import numpy as np
    return np.concatenate(chunks)


def create_wake_word_detector(stt) -> BaseWakeWordDetector:
    return FuzzyWakeWordDetector(stt)
