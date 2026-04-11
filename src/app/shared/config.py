from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        **kwargs: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        # .env file takes precedence over shell environment variables
        return (init_settings, dotenv_settings, *kwargs.values())

    # Server
    api_port: int = 8000
    web_port: int = 3000
    docs_port: int = 8100

    # OpenRouter
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_api_key: str = "sk-or-change-me"
    llm_model: str = "anthropic/claude-sonnet-4-20250514"

    # Database
    database_url: str = "sqlite+aiosqlite:///data/app.db"

    # Persistence
    checkpoint_db_path: str = "data/checkpoints.db"
    chroma_path: str = "data/chroma"

    # Logging
    log_level: str = "INFO"
    log_json: bool = False
