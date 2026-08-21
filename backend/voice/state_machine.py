"""
Stage 5: Voice State Machine.

Explicit states for the voice interaction pipeline.
All transitions are logged for debug visibility.
"""
from enum import Enum, auto
import logging

logger = logging.getLogger("backend.voice.state_machine")


class VoiceState(Enum):
    IDLE = auto()
    LISTENING_FOR_WAKE_WORD = auto()
    WAKE_WORD_DETECTED = auto()
    LISTENING_FOR_COMMAND = auto()
    PROCESSING = auto()
    EXECUTING_TOOL = auto()
    SPEAKING = auto()
    ERROR = auto()


class VoiceStateMachine:
    """Manages and logs voice state transitions."""

    def __init__(self):
        self._state = VoiceState.IDLE
        logger.info(f"[VOICE] State: {self._state.name}")

    @property
    def current_state(self) -> VoiceState:
        return self._state

    def transition(self, new_state: VoiceState):
        if new_state == self._state:
            return
        old = self._state.name
        self._state = new_state
        logger.info(f"[VOICE] State: {old} → {new_state.name}")

    def is_in(self, *states: VoiceState) -> bool:
        return self._state in states
