"""
Stage 5: SpeechRecognizer — STT abstraction.

Uses a sounddevice-based audio capture pipeline compatible with Python 3.14,
then feeds audio to Google Web Speech API via SpeechRecognition.

Falls back gracefully if any dependency is missing.
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
    """
    Capture audio from microphone using sounddevice,
    then transcribe it with Google Web Speech (free tier).
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1

    def __init__(self, silence_timeout: float = 1.2, command_timeout: float = 10.0):
        self.silence_timeout = silence_timeout
        self.command_timeout = command_timeout
        self._recognizer = sr.Recognizer() if _SR_AVAILABLE else None

    # ------------------------------------------------------------------
    def is_available(self) -> bool:
        return _SD_AVAILABLE and _SR_AVAILABLE

    # ------------------------------------------------------------------
    def _record(self, max_duration: float, silence_threshold: float = 300.0) -> Optional[bytes]:
        """
        Record audio until silence_timeout seconds of silence detected,
        or max_duration seconds have elapsed.

        Returns raw PCM bytes (16-bit, 16kHz, mono).
        """
        if not _SD_AVAILABLE:
            return None

        chunk_duration = 0.1  # 100ms chunks
        chunk_samples = int(self.SAMPLE_RATE * chunk_duration)
        silence_chunks_limit = int(self.silence_timeout / chunk_duration)

        frames = []
        silence_chunks = 0
        total_chunks = int(max_duration / chunk_duration)

        try:
            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                channels=self.CHANNELS,
                dtype="int16"
            ) as stream:
                for _ in range(total_chunks):
                    chunk, _ = stream.read(chunk_samples)
                    frames.append(chunk.copy())

                    # Simple amplitude-based voice activity detection
                    amplitude = np.abs(chunk).mean()
                    if amplitude < silence_threshold:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0

                    # Stop early if we detect sustained silence after hearing something
                    if len(frames) > 5 and silence_chunks >= silence_chunks_limit:
                        break

        except Exception as exc:
            logger.error(f"[STT] Recording error: {exc}")
            return None

        if not frames:
            return None

        audio_array = np.concatenate(frames, axis=0)
        return audio_array.tobytes()

    # ------------------------------------------------------------------
    def _pcm_to_audio_data(self, pcm_bytes: bytes) -> Optional[object]:
        """Wrap raw PCM bytes into a SpeechRecognition AudioData object."""
        if not _SR_AVAILABLE or self._recognizer is None:
            return None
        try:
            # Build a proper WAV in-memory so SR can process it
            buf = io.BytesIO()
            with wave.open(buf, "wb") as wf:
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(pcm_bytes)
            buf.seek(0)
            with sr.AudioFile(buf) as source:
                audio = self._recognizer.record(source)
            return audio
        except Exception as exc:
            logger.error(f"[STT] PCM→AudioData conversion failed: {exc}")
            return None

    # ------------------------------------------------------------------
    def transcribe(self, audio) -> Optional[str]:
        """Convert a SpeechRecognition AudioData object to text."""
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

    # ------------------------------------------------------------------
    def recognize(self) -> Optional[str]:
        """Full end-to-end: record microphone audio → return transcribed text."""
        if not self.is_available():
            logger.warning("[STT] recognize() called but STT is unavailable.")
            return None

        logger.debug("[STT] Recording...")
        pcm = self._record(max_duration=self.command_timeout)
        if not pcm:
            return None

        audio = self._pcm_to_audio_data(pcm)
        if not audio:
            return None

        return self.transcribe(audio)
