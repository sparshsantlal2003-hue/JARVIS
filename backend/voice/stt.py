"""
Stage 5: SpeechRecognizer — records until silence using sounddevice,
then transcribes via Google Web Speech API.

Uses energy-based VAD to know when user has finished speaking,
so commands are not cut off mid-sentence.
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
CHUNK_MS = 50
CHUNK_SIZE = int(TARGET_RATE * CHUNK_MS / 1000)
SPEECH_THRESHOLD = 400      # amplitude to consider as speech
SILENCE_CHUNKS = 20         # 20 × 50ms = 1s of silence ends recording
MAX_CHUNKS = 200            # 200 × 50ms = 10s max recording


class SpeechRecognizer:
    def __init__(self, silence_timeout: float = 1.2, command_timeout: float = 10.0):
        self.silence_timeout = silence_timeout
        self.command_timeout = command_timeout
        self._recognizer = sr.Recognizer() if _SR_AVAILABLE else None

    def is_available(self) -> bool:
        return _SD_AVAILABLE and _SR_AVAILABLE

    def _record_until_silence(self) -> Optional[bytes]:
        """
        Record audio chunks until silence is detected.
        Waits for speech to start first, then stops after silence.
        """
        if not _SD_AVAILABLE:
            return None

        frames = []
        silence_count = 0
        speech_started = False
        max_chunks = int(self.command_timeout * 1000 / CHUNK_MS)
        silence_limit = int(self.silence_timeout * 1000 / CHUNK_MS)

        try:
            with sd.InputStream(samplerate=TARGET_RATE, channels=1,
                                dtype="int16", blocksize=CHUNK_SIZE) as stream:
                for _ in range(max_chunks):
                    chunk, _ = stream.read(CHUNK_SIZE)
                    chunk_flat = chunk.flatten()
                    amp = float(np.abs(chunk_flat).mean())

                    if amp > SPEECH_THRESHOLD:
                        speech_started = True
                        silence_count = 0
                        frames.append(chunk_flat.copy())
                    else:
                        if speech_started:
                            frames.append(chunk_flat.copy())
                            silence_count += 1
                            if silence_count >= silence_limit:
                                break  # done — silence after speech
                        # If speech hasn't started yet, skip (don't record silence preamble)
        except Exception as exc:
            logger.error(f"[STT] Recording error: {exc}")
            return None

        if not frames:
            return None

        return np.concatenate(frames).astype("int16").tobytes()

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
        logger.debug("[STT] Waiting for speech...")
        pcm = self._record_until_silence()
        if not pcm:
            return None
        audio = self._pcm_to_audio_data(pcm)
        if not audio:
            return None
        return self.transcribe(audio)
