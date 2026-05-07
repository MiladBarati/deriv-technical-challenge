from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings and environment variables.
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM Keys
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.gapgpt.app/v1"
    DEFAULT_MODEL: str = "gapgpt-qwen-3.5"
    ANTHROPIC_API_KEY: Optional[str] = None

    # Application Configuration
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

settings = Settings()
