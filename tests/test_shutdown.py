"""
Tests for the ShutdownManager and is_shutdown_command() detector.
No real microphone, speakers, browser, or Windows GUI required.
"""
import pytest
from unittest.mock import MagicMock, patch
from backend.shutdown import is_shutdown_command, ShutdownManager, FAREWELL_MESSAGE


# ─── 1-7: Command detection ───────────────────────────────────────────────────

def test_exit_triggers_shutdown():
    assert is_shutdown_command("exit") is True

def test_quit_triggers_shutdown():
    assert is_shutdown_command("quit") is True

def test_shutdown_triggers_shutdown():
    assert is_shutdown_command("shutdown") is True

def test_close_jarvis_triggers_shutdown():
    assert is_shutdown_command("close jarvis") is True

def test_stop_jarvis_triggers_shutdown():
    assert is_shutdown_command("stop jarvis") is True

def test_case_insensitive():
    assert is_shutdown_command("EXIT") is True
    assert is_shutdown_command("Quit") is True
    assert is_shutdown_command("CLOSE JARVIS") is True
    assert is_shutdown_command("Shut Yourself Down") is True

def test_leading_trailing_whitespace():
    assert is_shutdown_command("  exit  ") is True
    assert is_shutdown_command("\tquit\n") is True
    assert is_shutdown_command("  shutdown jarvis  ") is True

# ─── 8: Ctrl+C cleanup (mocked) ───────────────────────────────────────────────

def test_keyboard_interrupt_cleanup():
    """ShutdownManager.shutdown() must call sys.exit(0) cleanly."""
    sm = ShutdownManager()
    sm.reset()
    with patch("sys.exit") as mock_exit:
        sm.shutdown(tts=None, wake_detector=None, speak_farewell=False)
        mock_exit.assert_called_once_with(0)

# ─── 9: Shutdown does NOT call the LLM ────────────────────────────────────────

def test_shutdown_bypasses_llm():
    """is_shutdown_command() must return True without any network/LLM call."""
    with patch("backend.agent.Agent.chat") as mock_chat:
        result = is_shutdown_command("exit")
        assert result is True
        mock_chat.assert_not_called()

# ─── 10: Idempotent shutdown ──────────────────────────────────────────────────

def test_shutdown_is_idempotent():
    sm = ShutdownManager()
    sm.reset()
    with patch("sys.exit") as mock_exit:
        sm.shutdown(tts=None, wake_detector=None, speak_farewell=False)
        sm.shutdown(tts=None, wake_detector=None, speak_farewell=False)
        # sys.exit should be called both times (cleanup is safe to repeat)
        assert mock_exit.call_count == 2

# ─── 11: Voice shutdown routes through ShutdownManager ───────────────────────

def test_voice_shutdown_uses_manager():
    from backend.shutdown import ShutdownManager
    sm = ShutdownManager()
    sm.reset()
    assert not sm.is_shutdown_requested()
    sm.request_shutdown()
    assert sm.is_shutdown_requested()
    sm.reset()  # cleanup for other tests

# ─── 12: Normal commands still reach the agent ───────────────────────────────

def test_normal_command_not_shutdown():
    assert is_shutdown_command("open brave") is False
    assert is_shutdown_command("what time is it") is False
    assert is_shutdown_command("play music") is False
    assert is_shutdown_command("hello") is False

# ─── False positive prevention ───────────────────────────────────────────────

def test_question_about_shutdown_not_triggered():
    assert is_shutdown_command("what command do I use to shut down jarvis") is False
    assert is_shutdown_command("how do I close jarvis") is False
    assert is_shutdown_command("can you shut down jarvis") is False
    assert is_shutdown_command("tell me how to exit") is False

# ─── Voice shutdown variants ─────────────────────────────────────────────────

def test_voice_shutdown_variants():
    assert is_shutdown_command("shut yourself down") is True
    assert is_shutdown_command("close yourself") is True
    assert is_shutdown_command("turn yourself off") is True
    assert is_shutdown_command("goodbye jarvis") is True
    assert is_shutdown_command("shut down jarvis") is True
    assert is_shutdown_command("goodbye") is True
    assert is_shutdown_command("shut down") is True

# ─── 13: Existing Stage 1-5 tests still work (import check) ──────────────────

def test_existing_modules_still_importable():
    import backend.agent
    import backend.provider
    import backend.tools.registry
    import backend.tools.windows_apps
    import backend.voice.loop
    import backend.voice.stt
    import backend.voice.tts
    import backend.voice.wake_word
