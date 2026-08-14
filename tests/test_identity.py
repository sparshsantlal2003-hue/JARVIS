import os
from unittest.mock import patch
from backend.provider import GeminiProvider

@patch('backend.provider.settings.gemini_api_key', 'dummy_key')
def test_jarvis_identity_instruction():
    provider = GeminiProvider()
    
    # We mock the client to see what it sends
    with patch.object(provider.client.models, 'generate_content') as mock_generate:
        try:
            provider.generate_response([], 'Who are you?')
        except Exception:
            pass # We just care about the mock being called
            
        assert mock_generate.called
        kwargs = mock_generate.call_args.kwargs
        contents = kwargs.get('contents', [])
        
        # Verify our strong identity injection is in the first element
        first_message = contents[0]
        assert first_message.role == 'user'
        assert 'JARVIS' in first_message.parts[0].text
        assert 'desktop AI assistant' in first_message.parts[0].text
