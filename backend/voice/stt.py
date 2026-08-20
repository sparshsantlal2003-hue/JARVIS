"""
Stage 5: SpeechRecognizer — STT abstraction with smart mic auto-selection.

Automatically uses the best available microphone (prefers Bluetooth headset),
re-detecting on every recognize() call so connecting/disconnecting earbuds
works without restarting JARVIS.
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
    logger.warning("[STT] sounddevice/numpy not available. Recording disabled.")

try:
    import speech_recognition as sr
    _SR_AVAILABLE = True
except ImportError:
    _SR_AVAILABLE = False
    logger.warning("[STT] SpeechRecognition not available. STT disabled.")


class SpeechRecognizer:
    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self, silence_timeout: float = 1.2, command_timeout: float = 10.0):
        self.silence_timeout = silence_timeout
        self.command_timeout = command_timeout
        self._recognizer = sr.Recognizer() if _SR_AVAILABLE else None

    def is_available(self) -> bool:
        return _SD_AVAILABLE and _SR_AVAILABLE

    def _get_device(self):
        """Re-scan for the best mic every time — handles BT connect/disconnect."""
        from backend.voice.mic_selector import get_best_device
        idx, name = get_best_device()
        logger.info(f"[STT] Using microphone: [{idx}] {name}")
        return idx

    def _record(self, max_duration: float, device_index=None, silence_threshold: float = 300.0) -> Optional[bytes]:
        if not _SD_AVAILABLE:
            return None

        chunk_duration = 0.1
        chunk_samples = int(self.SAMPLE_RATE * chunk_duration)
        silence_chunks_limit = int(self.silence_timeout / chunk_duration)
        total_chunks = int(max_duration / chunk_duration)
        frames = []
        silence_chunks = 0

        try:
            kwargs = dict(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="int16"
            )
            if device_index is not None:
                kwargs["device"] = device_index

            with sd.InputStream(**kwargs) as stream:
                for _ in range(total_chunks):
                    chunk, _ = stream.read(chunk_samples)
                    frames.append(chunk.copy())
                    amplitude = np.abs(chunk).mean()
                    if amplitude < silence_threshold:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0
                    if len(frames) > 5 and silence_chunks >= silence_chunks_limit:
                        break
        except Exception as exc:
            logger.error(f"[STT] Recording error on device [{device_index}]: {exc}")
            # Retry with system default if BT device failed
            if device_index is not None:
                logger.info("[STT] Retrying with system default microphone...")
                return self._record(max_duration, device_index=None, silence_threshold=silence_threshold)
            return None

        if not frames:
            return None
        return np.concatenate(frames, axis=0).tobytes()

    def _pcm_to_audio_data(self, pcm_bytes: bytes) -> Optional[object]:
        if not _SR_AVAILABLE or self._recognizer is None:
            return None
        try:
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(self.SAMPLE_RATE)
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
            logger.debug("[STT] Speech not understood.")
            return None
        except sr.RequestError as exc:
            logger.error(f"[STT] Google STT API error: {exc}")
            return None
        except Exception as exc:
            logger.error(f"[STT] Unexpected transcription error: {exc}")
            return None

    def recognize(self) -> Optional[str]:
        if not self.is_available():
            logger.warning("[STT] recognize() called but STT is unavailable.")
            return None
        device_index = self._get_device()
        pcm = self._record(max_duration=self.command_timeout, device_index=device_index)
        if not pcm:
            return None
        audio = self._pcm_to_audio_data(pcm)
        if not audio:
            return None
        return self.transcribe(audio)
