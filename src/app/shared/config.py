from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    # Server
    api_port: int = 8000
    web_port: int = 3000
    docs_port: int = 8100

    # LLM provider
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = "sk-or-change-me"
    llm_model: str = "anthropic/claude-sonnet-4-20250514"

    # Database
    database_url: str = "sqlite+aiosqlite:///data/app.db"

    # Logging
    log_level: str = "INFO"
    log_json: bool = False
