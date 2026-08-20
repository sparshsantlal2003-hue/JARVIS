from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Core
    ai_provider: str = "groq"
    gemini_api_key: str = "your_gemini_api_key_here"
    groq_api_key: str = "your_groq_api_key_here"
    groq_model: str = "llama-3.1-8b-instant"
    log_level: str = "INFO"

    # Stage 5 — Voice Interface
    voice_enabled: bool = False
    wake_word: str = "hello jarvis"
    voice_silence_timeout: float = 1.2
    voice_command_timeout: int = 10
    tts_enabled: bool = True
    stt_enabled: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
