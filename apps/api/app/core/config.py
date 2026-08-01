from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SportsIntel AI API"
    app_env: str = "development"
    app_version: str = "0.2.0"
    log_level: str = "INFO"

    public_url: str = "http://localhost:3300"
    next_public_api_url: str = "http://localhost:8300/api"

    db_host: str = "postgres"
    db_port: int = 5432
    db_name: str = "sportsintel"
    db_user: str = "sportsintel"
    db_password: str = Field(min_length=1)

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0

    jwt_secret: str = Field(min_length=32)
    jwt_expire_minutes: int = 1440  # legacy input, no longer used for access tokens
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    email_verification_expire_hours: int = 24
    password_reset_expire_minutes: int = 30
    login_max_attempts: int = 5
    login_lockout_minutes: int = 15
    mfa_issuer: str = "SportsIntel AI"
    auth_return_tokens_in_response: bool = True

    cors_origins: str = "http://localhost:3300"
    sports_data_provider: str = "demo"
    ollama_url: str = "http://host.docker.internal:11434"
    llm_model: str = "qwen3:14b"

    admin_bootstrap_email: str = "admin@discovera.ai"
    access_token_cookie: str = "sportsintel_access_token"
    refresh_token_cookie: str = "sportsintel_refresh_token"
    access_token_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return f"postgresql+psycopg://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def cors_origin_list(self) -> list[str]:
        return [v.strip() for v in self.cors_origins.split(",") if v.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
