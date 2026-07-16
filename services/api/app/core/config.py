"""Application settings."""

from urllib.parse import quote_plus, urlparse, urlunparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "hook.press API"
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://hookpress:hookpress_dev@localhost:5432/hookpress"
    db_host: str = ""
    db_port: int = 5432
    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "hookpress"
    s3_secret_key: str = "hookpress_dev_secret"
    s3_bucket_media: str = "hookpress-media"
    s3_use_ssl: bool = False

    cors_origins: str = "http://localhost:3000"
    dev_login_enabled: bool = True
    api_secret_key: str = "change-me-in-production-use-openssl-rand"

    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 30
    jwt_private_key_path: str = "certs/dev/private.pem"
    jwt_public_key_path: str = "certs/dev/public.pem"

    cookie_secure: bool = False
    refresh_cookie_name: str = "hookpress_refresh"

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_task_always_eager: bool = False
    presigned_url_ttl_seconds: int = 3600

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60

    promo_url: str = "http://promo:8081"

    distribution_webhook_secret: str = "change-me-distribution-webhook-secret"
    platform_commission_bps: int = 1000  # 10% in basis points
    media_upload_stale_hours: int = 24

    oauth_google_client_id: str = ""
    oauth_google_client_secret: str = ""
    oauth_yandex_client_id: str = ""
    oauth_yandex_client_secret: str = ""
    oauth_vk_client_id: str = ""
    oauth_vk_client_secret: str = ""
    oauth_apple_client_id: str = ""
    oauth_apple_team_id: str = ""
    oauth_google_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"
    oauth_yandex_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/yandex/callback"
    oauth_vk_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/vk/callback"
    oauth_apple_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/apple/callback"
    oauth_mock_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/mock/callback"
    oauth_state_ttl_seconds: int = 600

    login_lockout_max_attempts: int = 10
    login_lockout_ttl_seconds: int = 900

    security_csp: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' http://localhost:8000 http://localhost:3000; "
        "frame-ancestors 'none'"
    )
    security_hsts_max_age: int = 31536000

    @model_validator(mode="after")
    def normalize_deploy_urls(self) -> "Settings":
        self.database_url = self.database_url.strip().strip('"').strip("'")
        self.db_host = self.db_host.strip()
        self.db_user = self.db_user.strip()
        self.db_password = self.db_password.strip()
        self.db_name = self.db_name.strip()

        # Prefer Render-injected DB_* vars — avoids broken manual DATABASE_URL pastes.
        if self.db_host and self.db_user and self.db_password and self.db_name:
            user = quote_plus(self.db_user)
            password = quote_plus(self.db_password)
            port = self.db_port or 5432
            self.database_url = (
                f"postgresql+asyncpg://{user}:{password}"
                f"@{self.db_host}:{port}/{self.db_name}"
            )
        else:
            if self.database_url.startswith("postgres://"):
                self.database_url = self.database_url.replace(
                    "postgres://", "postgresql+asyncpg://", 1
                )
            elif self.database_url.startswith("postgresql://"):
                self.database_url = self.database_url.replace(
                    "postgresql://", "postgresql+asyncpg://", 1
                )

        parsed = urlparse(self.database_url)
        if parsed.query:
            self.database_url = urlunparse(parsed._replace(query=""))

        host = urlparse(self.database_url).hostname
        if not host:
            raise ValueError(
                "Database hostname missing. Set DB_HOST, DB_USER, DB_PASSWORD, DB_NAME "
                "on hookpress-api (from hookpress-db → Connect → Internal)."
            )

        if self.app_env == "production":
            self.cookie_secure = True
            self.dev_login_enabled = True
            if "localhost" in self.celery_broker_url and self.redis_url:
                self.celery_broker_url = self.redis_url
        return self

    @property
    def database_host(self) -> str:
        return urlparse(self.database_url).hostname or self.db_host or ""

    @property
    def database_connect_args(self) -> dict:
        """External Render Postgres (*.render.com) requires SSL; internal host does not."""
        host = self.database_host
        if host.endswith(".render.com"):
            return {"ssl": True}
        return {}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
