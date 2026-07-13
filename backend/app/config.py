from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    api_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    database_url: str = (
        "postgresql+asyncpg://orchestra:orchestra@localhost:5432/orchestra"
    )
    # Cloud Run + Cloud SQL Connector: PROJECT:REGION:INSTANCE
    cloud_sql_instance: str | None = None
    # "private" (VPC) or "public" — Cloud Run gen2 unix sockets break asyncpg
    cloud_sql_ip_type: str = "private"
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
    auto_create_all: bool = True

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 20.0
    # When true (or APP_ENV=production), Spec Compiler + Task Packet must use Gemini —
    # no silent fixture fallback. Set REQUIRE_GEMINI=true to force locally.
    require_gemini: bool = False

    auth_mode: str = "demo"
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None
    clerk_audience: str | None = None
    # Comma-separated emails allowed as admins when AUTH_MODE=clerk
    admin_email_allowlist: str = ""

    @property
    def db_connect_args(self) -> dict:
        # Unix sockets via /cloudsql/... break asyncpg on Cloud Run gen2
        # (NotADirectoryError). Use CLOUD_SQL_INSTANCE + Connector instead.
        return {}

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")

    @property
    def gemini_required(self) -> bool:
        return self.require_gemini or self.is_production

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)

    def ensure_gemini_configured(self) -> None:
        """Fail loud when Gemini is required but GEMINI_API_KEY is missing."""
        if self.gemini_required and not self.gemini_enabled:
            raise RuntimeError(
                "GEMINI_API_KEY is required when APP_ENV=production or REQUIRE_GEMINI=true. "
                "Set the key via Secret Manager on Cloud Run (see docs/DEPLOY_API.md). "
                "Silent fixture fallback is disabled for Spec Compiler and Task Packet."
            )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def admin_email_allowlist_set(self) -> set[str]:
        return {
            e.strip().lower()
            for e in self.admin_email_allowlist.split(",")
            if e.strip()
        }


settings = Settings()
