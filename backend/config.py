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

    # Stage 7 - Vision
    vision_enabled: bool = True
    vision_min_confidence: float = 0.80
    vision_max_retries: int = 2
    vision_model: str = "llama-3.2-11b-vision-preview"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
