"""Application configuration via pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All config from environment variables. Fails fast if required vars missing."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "example-app"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(default="postgresql+asyncpg://dev:dev@localhost:5432/app_dev")
    secret_key: str = Field(min_length=32, repr=False, default="change-me-to-a-random-32-plus-char-string")


settings = Settings()
