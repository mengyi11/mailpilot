from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "MailPilot API"
    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = (
        "postgresql+psycopg://mailpilot:mailpilot_dev@localhost:5432/mailpilot"
    )
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    google_oauth_scopes: list[str] = [
        "https://www.googleapis.com/auth/gmail.readonly"
    ]
    oauth_state_secret: str = ""
    oauth_state_max_age_seconds: int = 600
    token_encryption_key: str = ""
    token_encryption_key_version: str = "v1"
    frontend_oauth_success_url: str = "http://localhost:3000/settings/accounts"
    gmail_sync_limit: int = 100
    gmail_sync_concurrency: int = 5
    gmail_sync_max_retries: int = 3


@lru_cache
def get_settings() -> Settings:
    return Settings()
