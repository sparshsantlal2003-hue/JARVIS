"""
Stage 5: SpeechRecognizer — simple STT using the system default microphone.
Records audio via sounddevice, sends to Google Web Speech API.
"""
import io
import logging
import wave
from typing import Optional

logger = logging.getLogger("backend.voice.stt")

try:
    import numpy as np
    import sounddevice as sd
    _SD_AVAILABLE = True
except ImportError:
    _SD_AVAILABLE = False
    logger.warning("[STT] sounddevice/numpy not available.")

try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False
    logger.warning("[STT] SpeechRecognition not available.")

TARGET_RATE = 16000


class SpeechRecognizer:
    def __init__(self, silence_timeout: float = 1.2, command_timeout: float = 10.0):
        self.silence_timeout = silence_timeout
        self.command_timeout = command_timeout
        self._recognizer = sr.Recognizer() if _SR_AVAILABLE else None

    def is_available(self) -> bool:
        return _SD_AVAILABLE and _SR_AVAILABLE

    def _record(self, max_duration: float) -> Optional[bytes]:
        if not _SD_AVAILABLE:
            return None
        import numpy as np
        n_samples = int(TARGET_RATE * max_duration)
        try:
            audio_array = sd.rec(n_samples, samplerate=TARGET_RATE,
                                 channels=1, dtype="int16", blocking=True)
            return audio_array.tobytes()
        except Exception as exc:
            logger.error(f"[STT] Recording error: {exc}")
            return None

    def _pcm_to_audio_data(self, pcm_bytes: bytes) -> Optional[object]:
        if not _SR_AVAILABLE or self._recognizer is None:
            return None
        try:
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(TARGET_RATE)
                wf.writeframes(pcm_bytes)
            buf.seek(0)
            with sr.AudioFile(buf) as source:
                audio = self._recognizer.record(source)
            return audio
        except Exception as exc:
            logger.error(f"[STT] PCM conversion failed: {exc}")
            return None

    def transcribe(self, audio) -> Optional[str]:
        if self._recognizer is None:
            return None
        try:
            text = self._recognizer.recognize_google(audio)
            logger.info(f"[STT] Transcription: \"{text}\"")
            return text.strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as exc:
            logger.error(f"[STT] Google STT API error: {exc}")
            return None
        except Exception as exc:
            logger.error(f"[STT] Error: {exc}")
            return None

    def recognize(self) -> Optional[str]:
        if not self.is_available():
            return None
        pcm = self._record(max_duration=self.command_timeout)
        if not pcm:
            return None
        audio = self._pcm_to_audio_data(pcm)
        if not audio:
            return None
        return self.transcribe(audio)
