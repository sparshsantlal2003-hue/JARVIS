"""
Stage 5: VoiceLoop — with graceful shutdown support.
"""
import logging
import time
import sys
from typing import TYPE_CHECKING

from backend.voice.state_machine import VoiceStateMachine, VoiceState
from backend.voice.stt import SpeechRecognizer
from backend.voice.tts import TextToSpeech
from backend.voice.wake_word import create_wake_word_detector
from backend.config import settings
from backend.shutdown import shutdown_manager, is_shutdown_command

if TYPE_CHECKING:
    from backend.agent import Agent

logger = logging.getLogger("backend.voice.loop")


def _print_status(msg: str):
    print(f"[VOICE] {msg}", flush=True)


class VoiceLoop:
    def __init__(self, agent: "Agent"):
        self._agent = agent
        self._state_machine = VoiceStateMachine()
        self._tts = TextToSpeech()
        self._stt = SpeechRecognizer(
            silence_timeout=settings.voice_silence_timeout,
            command_timeout=settings.voice_command_timeout,
        )
        self._wake_detector = create_wake_word_detector(self._stt)
        self._running = False
        self.paused = False

    def _speak(self, text: str):
        logger.info(f"[TTS] \"{text}\"")
        self._state_machine.transition(VoiceState.SPEAKING)
        try:
            self._tts.speak_and_wait(text)
        except Exception as exc:
            logger.error(f"[TTS] Failed: {exc}")

    def _listen_for_command(self):
        self._state_machine.transition(VoiceState.LISTENING_FOR_COMMAND)
        _print_status("Listening for your command... (speak now)")
        text = self._stt.recognize()
        if text:
            print(f"[STT] Heard: \"{text}\"", flush=True)
        return text

    def _process_command(self, command: str) -> str:
        self._state_machine.transition(VoiceState.PROCESSING)
        _print_status(f"Processing: \"{command}\"")
        try:
            response = self._agent.chat(command)
            return response
        except Exception as exc:
            logger.error(f"[AGENT] Error: {exc}")
            return "I encountered an error. Please try again."

    def _cleanup(self):
        """Stop all owned resources cleanly."""
        try:
            self._wake_detector.stop()
        except Exception:
            pass
        try:
            self._tts.stop()
        except Exception:
            pass
        self._running = False

    def run(self):
        if not self._stt.is_available():
            _print_status("Voice mode unavailable — STT/mic not ready. Use text mode.")
            return

        if not self._tts.is_available():
            _print_status("Warning: TTS unavailable. Responses will be text-only.")

        self._running = True
        shutdown_manager.reset()
        self._wake_detector.start()

        print("\n" + "=" * 50)
        print("  JARVIS Stage 5 — Voice Mode")
        print(f"  Wake phrase: \"{settings.wake_word}\"")
        print("  Say 'shut yourself down' or press Ctrl+C to exit.")
        print("=" * 50 + "\n")

        try:
            while self._running and not shutdown_manager.is_shutdown_requested():
                self._state_machine.transition(VoiceState.LISTENING_FOR_WAKE_WORD)
                _print_status(f"Listening for wake word: \"{settings.wake_word}\" ...")

                if self.paused:
                    time.sleep(1.0)
                    continue

                wake_detected = False
                try:
                    wake_detected = self._wake_detector.detect()
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    logger.warning(f"[VOICE] Wake-word error: {exc}")
                    time.sleep(0.5)
                    continue

                if not wake_detected:
                    continue

                self._state_machine.transition(VoiceState.WAKE_WORD_DETECTED)
                _print_status("Wake word detected!")
                self._speak("Yes?")

                command = None
                try:
                    command = self._listen_for_command()
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    logger.warning(f"[VOICE] STT error: {exc}")

                if not command:
                    _print_status("Did not catch that. Returning to wake word.")
                    self._speak("Sorry, I didn't catch that.")
                    self._state_machine.transition(VoiceState.IDLE)
                    continue

                # ── Deterministic shutdown check (before LLM) ──────────
                if is_shutdown_command(command):
                    logger.info("[SHUTDOWN] Shutdown command detected via voice.")
                    self._cleanup()
                    shutdown_manager.shutdown(
                        tts=self._tts,
                        wake_detector=self._wake_detector,
                        speak_farewell=True
                    )
                    return

                # ── Normal command → agent ─────────────────────────────
                response = "I encountered an error. Please try again."
                try:
                    response = self._process_command(command)
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    logger.error(f"[VOICE] Processing error: {exc}")

                _print_status(f"Response: \"{response[:80]}\"")
                self._speak(response)
                self._state_machine.transition(VoiceState.IDLE)
                _print_status("Returning to wake-word detection.\n")

        except KeyboardInterrupt:
            print()
            self._cleanup()
            shutdown_manager.shutdown(
                tts=self._tts,
                wake_detector=self._wake_detector,
                speak_farewell=False
            )
        finally:
            self._cleanup()
