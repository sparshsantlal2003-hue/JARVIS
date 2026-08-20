"""
Stage 5: VoiceLoop — the main conversational voice interaction loop.

Wires together:
  WakeWordDetector → SpeechRecognizer → Agent.chat() → TextToSpeech

Uses the EXISTING Agent instance (no new agent is created).
Conversation history is preserved across voice interactions.
"""
import logging
import time
from typing import TYPE_CHECKING

from backend.voice.state_machine import VoiceStateMachine, VoiceState
from backend.voice.stt import SpeechRecognizer
from backend.voice.tts import TextToSpeech
from backend.voice.wake_word import create_wake_word_detector
from backend.config import settings

if TYPE_CHECKING:
    from backend.agent import Agent

logger = logging.getLogger("backend.voice.loop")


class VoiceLoop:
    """
    Main voice interaction loop.

    Usage:
        agent = Agent()
        loop = VoiceLoop(agent)
        loop.run()
    """

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

    # ------------------------------------------------------------------
    def _speak(self, text: str):
        """Speak and log."""
        logger.info(f"[TTS] \"{text}\"")
        self._state_machine.transition(VoiceState.SPEAKING)
        self._tts.speak_and_wait(text)

    # ------------------------------------------------------------------
    def _listen_for_command(self) -> str | None:
        """Record and transcribe the user's command."""
        self._state_machine.transition(VoiceState.LISTENING_FOR_COMMAND)
        logger.info("[VOICE] Listening for command...")
        text = self._stt.recognize()
        if text:
            logger.info(f"[STT] \"{text}\"")
        return text

    # ------------------------------------------------------------------
    def _process_command(self, command: str) -> str:
        """Send the command to the JARVIS agent and get a response."""
        self._state_machine.transition(VoiceState.PROCESSING)
        logger.info(f"[AGENT] Processing command: \"{command}\"")
        try:
            response = self._agent.chat(command)
            return response
        except Exception as exc:
            logger.error(f"[AGENT] Error processing command: {exc}")
            return "I encountered an error. Please try again."

    # ------------------------------------------------------------------
    def run(self):
        """Main blocking loop. Press Ctrl+C to exit."""
        if not self._stt.is_available():
            logger.error(
                "[VOICE] STT unavailable (sounddevice or SpeechRecognition not installed). "
                "Voice mode cannot start. Use text mode instead."
            )
            print("\n[VOICE] Voice mode is unavailable on this machine.")
            print("[VOICE] Please use text mode: python -m backend.main --text\n")
            return

        if not self._tts.is_available():
            logger.warning("[VOICE] TTS unavailable. JARVIS will not speak responses.")

        self._running = True
        self._wake_detector.start()

        print("\n" + "=" * 50)
        print("  JARVIS Stage 5 — Voice Mode")
        print(f"  Wake phrase: \"{settings.wake_word}\"")
        print("  Press Ctrl+C to exit.")
        print("=" * 50 + "\n")

        try:
            while self._running:
                self._state_machine.transition(VoiceState.LISTENING_FOR_WAKE_WORD)
                logger.info("[VOICE] Listening for wake word...")

                # ── WAKE WORD PHASE ───────────────────────────────────
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
                    continue  # Back to listening

                # ── ACTIVATION ────────────────────────────────────────
                self._state_machine.transition(VoiceState.WAKE_WORD_DETECTED)
                logger.info("[VOICE] Wake word detected")
                self._speak("Yes?")

                # ── COMMAND PHASE ─────────────────────────────────────
                command = None
                try:
                    command = self._listen_for_command()
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    logger.warning(f"[VOICE] STT error: {exc}")

                if not command:
                    self._speak("Sorry, I didn't catch that.")
                    self._state_machine.transition(VoiceState.IDLE)
                    continue

                # ── PROCESSING ────────────────────────────────────────
                response = "I encountered an error. Please try again."
                try:
                    response = self._process_command(command)
                except KeyboardInterrupt:
                    raise
                except Exception as exc:
                    logger.error(f"[VOICE] Unexpected error during processing: {exc}")

                # ── SPEAK RESPONSE ────────────────────────────────────
                try:
                    self._speak(response)
                except Exception as tts_exc:
                    logger.error(f"[TTS] Failed to speak response: {tts_exc}")
                self._state_machine.transition(VoiceState.IDLE)
                logger.info("[VOICE] Returning to wake-word detection.")

        except KeyboardInterrupt:
            print("\n[VOICE] Voice mode stopped.")
        finally:
            self._wake_detector.stop()
            self._tts.stop()
            self._running = False
            logger.info("[VOICE] Voice loop shut down cleanly.")

