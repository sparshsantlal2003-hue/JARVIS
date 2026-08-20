"""
Stage 5: SpeechRecognizer — STT using WASAPI (48kHz) → downsample → Google STT.
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


TARGET_RATE = 16000  # Google STT requires 16kHz


def _downsample(audio: "np.ndarray", src_rate: int, dst_rate: int = TARGET_RATE) -> "np.ndarray":
    """Simple integer-ratio downsampling (no scipy needed)."""
    if src_rate == dst_rate:
        return audio
    import numpy as np
    if audio.ndim > 1:
        audio = audio[:, 0]  # take first channel (mono)
    ratio = src_rate / dst_rate
    new_len = int(len(audio) / ratio)
    indices = (np.arange(new_len) * ratio).astype(int)
    return audio[indices]


class SpeechRecognizer:
    def __init__(self, silence_timeout: float = 1.2, command_timeout: float = 10.0):
        self.silence_timeout = silence_timeout
        self.command_timeout = command_timeout
        self._recognizer = sr.Recognizer() if _SR_AVAILABLE else None

    def is_available(self) -> bool:
        return _SD_AVAILABLE and _SR_AVAILABLE

    def _get_device(self):
        from backend.voice.mic_selector import get_best_device
        return get_best_device()

    def _record(self, max_duration: float,
                device_index=None, native_rate: int = 16000,
                silence_threshold: float = 150.0) -> Optional[bytes]:
        if not _SD_AVAILABLE:
            return None
        import numpy as np

        channels = 2 if native_rate == 48000 else 1
        chunk_duration = 0.1
        chunk_samples = int(native_rate * chunk_duration)
        silence_chunks_limit = int(self.silence_timeout / chunk_duration)
        total_chunks = int(max_duration / chunk_duration)
        frames = []
        silence_chunks = 0

        try:
            kwargs = dict(samplerate=native_rate, channels=channels, dtype="int16")
            if device_index is not None:
                kwargs["device"] = device_index

            with sd.InputStream(**kwargs) as stream:
                for _ in range(total_chunks):
                    chunk, _ = stream.read(chunk_samples)
                    frames.append(chunk.copy())
                    amplitude = float(np.abs(chunk).mean())
                    if amplitude < silence_threshold:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0
                    if len(frames) > 5 and silence_chunks >= silence_chunks_limit:
                        break
        except Exception as exc:
            logger.error(f"[STT] Recording error: {exc}")
            return None

        if not frames:
            return None

        audio_array = np.concatenate(frames, axis=0)
        # Downsample to 16kHz mono for Google STT
        mono = _downsample(audio_array, native_rate, TARGET_RATE)
        return mono.astype("int16").tobytes()

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
        idx, name, rate = self._get_device()
        logger.info(f"[STT] Recording via [{idx}] {name} @ {rate}Hz")
        pcm = self._record(max_duration=self.command_timeout,
                           device_index=idx, native_rate=rate)
        if not pcm:
            return None
        audio = self._pcm_to_audio_data(pcm)
        if not audio:
            return None
        return self.transcribe(audio)
