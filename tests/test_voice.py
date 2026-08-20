"""
Stage 5 — Voice Interface Unit Tests

All tests use mocks. No real microphone, speakers, or audio device required.
CI-safe.
"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# ─────────────────────────────────────────────────────────────────────────────
# 1. Voice config loads correctly
# ─────────────────────────────────────────────────────────────────────────────
def test_voice_config_loads():
    from backend.config import Settings
    with patch.dict("os.environ", {
        "AI_PROVIDER": "mock",
        "VOICE_ENABLED": "true",
        "WAKE_WORD": "hey jarvis",
        "VOICE_SILENCE_TIMEOUT": "2.0",
        "VOICE_COMMAND_TIMEOUT": "15",
        "TTS_ENABLED": "true",
        "STT_ENABLED": "true",
    }):
        s = Settings()
        assert s.voice_enabled is True
        assert s.wake_word == "hey jarvis"
        assert s.voice_silence_timeout == 2.0
        assert s.voice_command_timeout == 15
        assert s.tts_enabled is True
        assert s.stt_enabled is True


# ─────────────────────────────────────────────────────────────────────────────
# 2. VoiceInput reports unavailable when no mic
# ─────────────────────────────────────────────────────────────────────────────
def test_voice_input_unavailable_when_no_mic():
    # When SR is not installed, VoiceInput must report unavailable without crashing
    from backend.voice.microphone import VoiceInput
    vi = VoiceInput()
    # With SR not installed in this env, is_available() must return False
    result = vi.is_available()
    assert result is False
    # And start() must return False gracefully
    assert vi.start() is False


# ─────────────────────────────────────────────────────────────────────────────
# 3. VoiceInput.start() returns False gracefully when unavailable
# ─────────────────────────────────────────────────────────────────────────────
def test_voice_input_start_graceful_failure():
    with patch("backend.voice.microphone._SR_AVAILABLE", False):
        from importlib import reload
        import backend.voice.microphone as mic_mod
        reload(mic_mod)
        vi = mic_mod.VoiceInput()
        result = vi.start()
        assert result is False


# ─────────────────────────────────────────────────────────────────────────────
# 4. WakeWordDetector can be mocked and detect() returns True on phrase match
# ─────────────────────────────────────────────────────────────────────────────
def test_wake_word_detector_mock():
    mock_stt = MagicMock()
    with patch("backend.config.settings") as mock_settings:
        mock_settings.wake_word = "hello jarvis"
        from backend.voice.wake_word import FuzzyWakeWordDetector
        detector = FuzzyWakeWordDetector(mock_stt, wake_phrase="hello jarvis")
        detector.start()
        assert detector.is_running() is True
        assert detector._is_wake_phrase("hello jarvis") is True
        assert detector._is_wake_phrase("hey jarvis what time is it") is True
        assert detector._is_wake_phrase("open brave") is False
        detector.stop()
        assert detector.is_running() is False


# ─────────────────────────────────────────────────────────────────────────────
# 5. SpeechRecognizer.is_available() returns False when deps missing
# ─────────────────────────────────────────────────────────────────────────────
def test_stt_unavailable_when_deps_missing():
    with patch("backend.voice.stt._SD_AVAILABLE", False), \
         patch("backend.voice.stt._SR_AVAILABLE", False):
        from importlib import reload
        import backend.voice.stt as stt_mod
        reload(stt_mod)
        stt = stt_mod.SpeechRecognizer()
        assert stt.is_available() is False
        assert stt.recognize() is None


# ─────────────────────────────────────────────────────────────────────────────
# 6. TextToSpeech.is_available() returns False when pyttsx3 missing
# ─────────────────────────────────────────────────────────────────────────────
def test_tts_unavailable_when_pyttsx3_missing():
    with patch("backend.voice.tts._PYTTSX3_AVAILABLE", False):
        from importlib import reload
        import backend.voice.tts as tts_mod
        reload(tts_mod)
        tts = tts_mod.TextToSpeech()
        assert tts.is_available() is False
        # Must not crash
        tts.speak("hello")
        tts.stop()


# ─────────────────────────────────────────────────────────────────────────────
# 7. Voice state machine transitions correctly
# ─────────────────────────────────────────────────────────────────────────────
def test_state_machine_transitions():
    from backend.voice.state_machine import VoiceStateMachine, VoiceState
    sm = VoiceStateMachine()
    assert sm.current_state == VoiceState.IDLE

    sm.transition(VoiceState.LISTENING_FOR_WAKE_WORD)
    assert sm.current_state == VoiceState.LISTENING_FOR_WAKE_WORD

    sm.transition(VoiceState.WAKE_WORD_DETECTED)
    assert sm.current_state == VoiceState.WAKE_WORD_DETECTED

    sm.transition(VoiceState.LISTENING_FOR_COMMAND)
    sm.transition(VoiceState.PROCESSING)
    sm.transition(VoiceState.SPEAKING)
    sm.transition(VoiceState.IDLE)
    assert sm.current_state == VoiceState.IDLE


# ─────────────────────────────────────────────────────────────────────────────
# 8. VoiceLoop: wake word detection activates command listening
# ─────────────────────────────────────────────────────────────────────────────
def test_voice_loop_wake_activates_command():
    from backend.voice.state_machine import VoiceState

    mock_agent = MagicMock()
    mock_agent.chat.return_value = "Done."

    with patch("backend.voice.loop.SpeechRecognizer") as MockSTT, \
         patch("backend.voice.loop.TextToSpeech") as MockTTS, \
         patch("backend.voice.loop.create_wake_word_detector") as MockWWD, \
         patch("backend.config.settings") as mock_settings:

        mock_settings.voice_silence_timeout = 1.2
        mock_settings.voice_command_timeout = 10
        mock_settings.wake_word = "hello jarvis"

        mock_stt_inst = MockSTT.return_value
        mock_stt_inst.is_available.return_value = True
        mock_stt_inst.recognize.return_value = "open brave"

        mock_tts_inst = MockTTS.return_value
        mock_tts_inst.is_available.return_value = True

        mock_wwd_inst = MockWWD.return_value
        # First call detects wake, second raises KeyboardInterrupt to exit loop
        mock_wwd_inst.detect.side_effect = [True, KeyboardInterrupt]

        from backend.voice.loop import VoiceLoop
        loop = VoiceLoop(mock_agent)
        loop.run()

        # Agent must have been called with the transcribed command
        mock_agent.chat.assert_called_once_with("open brave")


# ─────────────────────────────────────────────────────────────────────────────
# 9. Transcribed commands reach the existing agent
# ─────────────────────────────────────────────────────────────────────────────
def test_transcribed_command_reaches_agent():
    mock_agent = MagicMock()
    mock_agent.chat.return_value = "Opened Brave."

    with patch("backend.voice.loop.SpeechRecognizer") as MockSTT, \
         patch("backend.voice.loop.TextToSpeech") as MockTTS, \
         patch("backend.voice.loop.create_wake_word_detector") as MockWWD, \
         patch("backend.config.settings") as mock_settings:

        mock_settings.voice_silence_timeout = 1.2
        mock_settings.voice_command_timeout = 10
        mock_settings.wake_word = "hello jarvis"

        MockSTT.return_value.is_available.return_value = True
        MockSTT.return_value.recognize.return_value = "open brave browser"
        MockTTS.return_value.is_available.return_value = True
        MockWWD.return_value.detect.side_effect = [True, KeyboardInterrupt]

        from backend.voice.loop import VoiceLoop
        loop = VoiceLoop(mock_agent)
        loop.run()

        mock_agent.chat.assert_called_with("open brave browser")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Agent response reaches TTS
# ─────────────────────────────────────────────────────────────────────────────
def test_agent_response_reaches_tts():
    mock_agent = MagicMock()
    mock_agent.chat.return_value = "Opening Brave."

    with patch("backend.voice.loop.SpeechRecognizer") as MockSTT, \
         patch("backend.voice.loop.TextToSpeech") as MockTTS, \
         patch("backend.voice.loop.create_wake_word_detector") as MockWWD, \
         patch("backend.config.settings") as mock_settings:

        mock_settings.voice_silence_timeout = 1.2
        mock_settings.voice_command_timeout = 10
        mock_settings.wake_word = "hello jarvis"

        MockSTT.return_value.is_available.return_value = True
        MockSTT.return_value.recognize.return_value = "open brave"
        mock_tts = MockTTS.return_value
        mock_tts.is_available.return_value = True
        MockWWD.return_value.detect.side_effect = [True, KeyboardInterrupt]

        from backend.voice.loop import VoiceLoop
        loop = VoiceLoop(mock_agent)
        loop.run()

        # speak_and_wait is called with the agent response
        calls = [str(c) for c in mock_tts.speak_and_wait.call_args_list]
        assert any("Opening Brave" in c for c in calls)


# ─────────────────────────────────────────────────────────────────────────────
# 11. STT failure is handled gracefully (returns to idle)
# ─────────────────────────────────────────────────────────────────────────────
def test_stt_failure_handled():
    mock_agent = MagicMock()

    with patch("backend.voice.loop.SpeechRecognizer") as MockSTT, \
         patch("backend.voice.loop.TextToSpeech") as MockTTS, \
         patch("backend.voice.loop.create_wake_word_detector") as MockWWD, \
         patch("backend.config.settings") as mock_settings:

        mock_settings.voice_silence_timeout = 1.2
        mock_settings.voice_command_timeout = 10
        mock_settings.wake_word = "hello jarvis"

        MockSTT.return_value.is_available.return_value = True
        MockSTT.return_value.recognize.return_value = None  # STT fails
        MockTTS.return_value.is_available.return_value = True
        MockWWD.return_value.detect.side_effect = [True, KeyboardInterrupt]

        from backend.voice.loop import VoiceLoop
        loop = VoiceLoop(mock_agent)
        loop.run()

        # Agent must NOT have been called
        mock_agent.chat.assert_not_called()


# ─────────────────────────────────────────────────────────────────────────────
# 12. TTS failure does not crash JARVIS
# ─────────────────────────────────────────────────────────────────────────────
def test_tts_failure_does_not_crash():
    mock_agent = MagicMock()
    mock_agent.chat.return_value = "Done."

    with patch("backend.voice.loop.SpeechRecognizer") as MockSTT, \
         patch("backend.voice.loop.TextToSpeech") as MockTTS, \
         patch("backend.voice.loop.create_wake_word_detector") as MockWWD, \
         patch("backend.config.settings") as mock_settings:

        mock_settings.voice_silence_timeout = 1.2
        mock_settings.voice_command_timeout = 10
        mock_settings.wake_word = "hello jarvis"

        MockSTT.return_value.is_available.return_value = True
        MockSTT.return_value.recognize.return_value = "open brave"
        MockTTS.return_value.is_available.return_value = True
        MockTTS.return_value.speak_and_wait.side_effect = [None, RuntimeError("TTS boom"), KeyboardInterrupt]
        MockWWD.return_value.detect.return_value = True

        from backend.voice.loop import VoiceLoop
        loop = VoiceLoop(mock_agent)
        # Should not raise
        try:
            loop.run()
        except RuntimeError:
            pytest.fail("TTS RuntimeError should have been caught by the loop!")
        except KeyboardInterrupt:
            pass  # Expected exit


# ─────────────────────────────────────────────────────────────────────────────
# 13. Microphone failure does not crash JARVIS (voice mode exits cleanly)
# ─────────────────────────────────────────────────────────────────────────────
def test_microphone_failure_no_crash():
    mock_agent = MagicMock()

    with patch("backend.voice.loop.SpeechRecognizer") as MockSTT, \
         patch("backend.voice.loop.TextToSpeech") as MockTTS, \
         patch("backend.voice.loop.create_wake_word_detector") as MockWWD, \
         patch("backend.config.settings") as mock_settings:

        mock_settings.voice_silence_timeout = 1.2
        mock_settings.voice_command_timeout = 10
        mock_settings.wake_word = "hello jarvis"

        # STT reports it is NOT available (simulates missing mic/deps)
        MockSTT.return_value.is_available.return_value = False
        MockTTS.return_value.is_available.return_value = True

        from backend.voice.loop import VoiceLoop
        loop = VoiceLoop(mock_agent)
        # Should return gracefully without crashing
        loop.run()
        mock_agent.chat.assert_not_called()


