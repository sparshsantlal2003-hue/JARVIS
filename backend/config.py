from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ai_provider: str = "gemini"
    gemini_api_key: str = "your_gemini_api_key_here"
    groq_api_key: str = "your_groq_api_key_here"
    groq_model: str = "llama-3.1-8b-instant"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
