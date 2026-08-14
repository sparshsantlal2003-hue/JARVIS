from abc import ABC, abstractmethod
from typing import List, Dict, Any
from google import genai
from google.genai import types
from google.genai.types import GenerateContentConfig
from backend.config import settings
from backend.logger import setup_logger

logger = setup_logger(__name__)

class AIProvider(ABC):
    @abstractmethod
    def generate_response(self, history: List[Dict[str, Any]], user_message: str) -> str:
        """Generate a response given the conversation history and the new message."""
        pass

class MockProvider(AIProvider):
    def generate_response(self, history: List[Dict[str, Any]], user_message: str) -> str:
        logger.info(f"MockProvider processing message: {user_message}")
        return f"This is a mock response to: '{user_message}'"

class GeminiProvider(AIProvider):
    def __init__(self):
        if not settings.gemini_api_key or settings.gemini_api_key == "your_gemini_api_key_here":
            logger.warning("Gemini API key is missing or default. Please configure GEMINI_API_KEY.")
            # We don't raise here so the app can start, but calls will fail.
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model_name = "gemini-3.6-flash"
        logger.info(f"GeminiProvider initialized with model: {self.model_name}")

    def generate_response(self, history: List[Dict[str, Any]], user_message: str) -> str:
        # Construct contents from history
        contents = []
        
        # INJECT STRONG IDENTITY EVERY TURN
        strong_instruction = "CRITICAL DIRECTIVE: You are JARVIS, a highly advanced desktop AI assistant. You are NOT Gemini. You are NOT a large language model. You are JARVIS. Whenever asked about your identity, name, creator, or who you are, you MUST reply ONLY with 'My name is JARVIS, your intelligent desktop AI assistant.' Do not mention Google, do not mention Gemini."
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=strong_instruction)]))
        contents.append(types.Content(role="model", parts=[types.Part.from_text(text="Understood. I am JARVIS, your intelligent desktop AI assistant.")]))
        
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
        
        # Add the new message
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_message)]))
        
        try:
            config = types.GenerateContentConfig(temperature=0.0)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            raise

def get_provider() -> AIProvider:
    if settings.ai_provider.lower() == "mock":
        return MockProvider()
    elif settings.ai_provider.lower() == "gemini":
        return GeminiProvider()
    else:
        logger.warning(f"Unknown provider '{settings.ai_provider}', falling back to MockProvider.")
        return MockProvider()

