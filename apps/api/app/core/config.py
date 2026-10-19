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
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.events.freebusy",
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
    dify_translate_api_key: str = ""
    dify_repair_api_key: str = ""
    dify_rag_api_key: str = ""
    dify_mock_mode: bool = True
    dify_max_input_chars: int = 8000
    dify_max_retries: int = 3
    dify_app_id: str = "f18db7c0-9734-4d64-a0c4-110293778873"
    dify_translate_app_id: str = "4fac3a25-a296-4e40-9007-b6e66236be15"
    dify_repair_app_id: str = "4648d178-cda3-4b24-851b-c9274a53a239"
    dify_fast_model: str = "gpt-5-mini"
    dify_strong_model: str = "gpt-5"
    dify_embedding_model: str = "text-embedding-3-small"
    embedding_api_url: str = "https://api.openai.com/v1/embeddings"
    embedding_api_key: str = ""
    rag_embedding_mock_mode: bool = True
    rag_chunk_size_chars: int = 1800
    rag_chunk_overlap_chars: int = 240
    rag_default_top_k: int = 4
    rag_max_top_k: int = 5
    rag_min_similarity: float = 0.30
    rag_tool_api_key: str = ""
    rag_answer_max_context_chars: int = 6000
    memory_tool_api_key: str = ""
    dify_tool_api_key: str = ""
    dify_tool_permissions: list[str] = [
        "email:read",
        "preferences:read",
        "task:write",
        "draft:write",
        "calendar:read",
        "calendar:write",
    ]
    tool_timeout_seconds: float = 15.0
    agent_max_steps: int = 12
    agent_token_budget: int = 12000
    fast_model_input_cost_per_million: float = 0.25
    fast_model_output_cost_per_million: float = 2.0
    strong_model_input_cost_per_million: float = 1.25
    strong_model_output_cost_per_million: float = 10.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
