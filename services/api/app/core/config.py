"""Application settings."""

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
        if self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        elif self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        if self.app_env == "production":
            self.cookie_secure = True
            self.dev_login_enabled = True
            if "localhost" in self.celery_broker_url and self.redis_url:
                self.celery_broker_url = self.redis_url
        return self

    @property
    def database_connect_args(self) -> dict:
        """Render Postgres requires SSL; asyncpg needs connect_args."""
        if self.is_production or "render.com" in self.database_url:
            return {"ssl": True}
        return {}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()
