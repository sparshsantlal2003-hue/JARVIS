from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ai_provider: str = "gemini"
    gemini_api_key: str = "your_gemini_api_key_here"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
