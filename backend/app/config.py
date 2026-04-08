"""Server configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite+aiosqlite:///./studio_captioner.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 72
    storage_base_path: str = ""
    default_asr_model: str = "whisper_cpp"
    default_whisper_model: str = "base"
    llm_api_base: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen2.5:7b"

    model_config = {"env_prefix": "SCA_", "env_file": ".env"}


settings = Settings()
