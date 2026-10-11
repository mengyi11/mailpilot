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
    gmail_sync_limit: int = 15
    gmail_sync_concurrency: int = 5
    gmail_sync_max_retries: int = 3
    email_user_timezone: str = "Asia/Singapore"
    attachment_max_size_bytes: int = 10 * 1024 * 1024
    attachment_max_per_email: int = 10
    dify_base_url: str = "https://api.dify.ai/v1"
    dify_api_key: str = ""
    dify_app_id: str = "f18db7c0-9734-4d64-a0c4-110293778873"
    dify_fast_model: str = "gpt-5-mini"
    dify_strong_model: str = "gpt-5"
    dify_embedding_model: str = "text-embedding-3-small"


@lru_cache
def get_settings() -> Settings:
    return Settings()
