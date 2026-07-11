from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    api_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    database_url: str = (
        "postgresql+asyncpg://orchestra:orchestra@localhost:5432/orchestra"
    )
    # Production pool tuning — pre_ping avoids stale-connection errors after DB restarts.
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_recycle_seconds: int = 1800

    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "orchestra-assets"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"

    secret_key: str = "change-me-in-production"
    auto_seed: bool = True
    # Dev convenience: create tables from models on boot. Set false in prod and
    # rely on `alembic upgrade head` (the versioned source of truth).
    auto_create_all: bool = True

    # --- Gemini AI gateway (key-ready; falls back to fixture when unset) ---
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 20.0

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
