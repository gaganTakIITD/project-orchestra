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
    # Prod target: raystartup:us-central1:orchestra-trial-pg (free-trial eligible)
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

    # AI auth — credit schema (docs/GCP_BILLING_SPLIT.md):
    #   off     → fixtures (local/dev default)
    #   vertex  → Vertex AI on VERTEX_PROJECT (raystartup free trial)
    # Never use Gemini Developer API / AI Studio API keys for Orchestra.
    gemini_auth: str = "off"
    vertex_project: str = "raystartup"
    vertex_location: str = "us-central1"
    # Deprecated / ignored — AI Studio keys are not trial-eligible. Kept so old
    # env files do not crash pydantic; must not enable the client.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    gemini_timeout_seconds: float = 15.0
    # When true (or APP_ENV=production), Spec Compiler must use Gemini —
    # no silent fixture fallback. Set REQUIRE_GEMINI=true to force locally.
    require_gemini: bool = False
    # Quote accept → build_plan. Default off: fixture DAG + packets (fast confirm).
    # Spec Compiler still uses Vertex. Set CONFIRM_AI_ENRICH=true for Vertex
    # Architect + per-task packets on confirm (slow: many sequential/parallel calls).
    confirm_ai_enrich: bool = False

    # Priority window before promote_backup (Technical Spec §6.3)
    priority_window_hours: float = 24.0
    # Background timer tick interval (0 = disabled; prefer Cloud Scheduler → /internal/timers/tick)
    timer_tick_seconds: float = 0.0

    auth_mode: str = "demo"
    clerk_jwks_url: str | None = None
    clerk_issuer: str | None = None
    clerk_audience: str | None = None
    # Comma-separated emails allowed as admins when AUTH_MODE=clerk
    admin_email_allowlist: str = ""

    # Sprint 5 — email + observability (optional)
    resend_api_key: str | None = None
    email_from: str | None = None
    sentry_dsn: str | None = None

    # Sprint 6 — payments sandbox (off by default)
    payments_enabled: bool = False
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None

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
        """True when Vertex AI on VERTEX_PROJECT is selected (not AI Studio keys)."""
        auth = (self.gemini_auth or "off").strip().lower()
        if auth != "vertex":
            return False
        return bool((self.vertex_project or "").strip())

    def ensure_gemini_configured(self) -> None:
        """Fail loud when Gemini is required but Vertex is not configured."""
        if self.gemini_api_key and self.is_production:
            raise RuntimeError(
                "GEMINI_API_KEY / Gemini Developer API (AI Studio) is forbidden in "
                "production. Use GEMINI_AUTH=vertex with VERTEX_PROJECT=raystartup "
                "(raystartup free trial). See docs/GCP_BILLING_SPLIT.md."
            )
        if self.gemini_required and not self.gemini_enabled:
            raise RuntimeError(
                "Vertex Gemini required when APP_ENV=production or REQUIRE_GEMINI=true. "
                "Set GEMINI_AUTH=vertex and VERTEX_PROJECT=raystartup. "
                "Do not use GEMINI_API_KEY (AI Studio) — not free-trial eligible. "
                "See docs/GCP_BILLING_SPLIT.md."
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
