import pytest
from unittest.mock import patch
from backend.config import Settings
from backend.agent import Agent
from backend.provider import MockProvider

def test_settings_default():
    # Test setting loading
    with patch.dict('os.environ', {'AI_PROVIDER': 'mock', 'GEMINI_API_KEY': 'test_key'}):
        settings = Settings()
        assert settings.ai_provider == "mock"
        assert settings.gemini_api_key == "test_key"
    
@patch("backend.config.settings.ai_provider", "mock")
def test_agent_history():
    agent = Agent()
    assert isinstance(agent.provider, MockProvider)
    
    assert len(agent.history) == 0
    
    reply = agent.chat("Hello JARVIS")
    
    assert "mock response" in reply.lower()
    assert len(agent.history) == 2
    assert agent.history[0]["role"] == "user"
    assert agent.history[0]["content"] == "Hello JARVIS"
    assert agent.history[1]["role"] == "assistant"
    assert agent.history[1]["content"] == reply
