"""Worker configuration."""

import os


class WorkerSettings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://hookpress:hookpress_dev@localhost:5432/hookpress",
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "hookpress")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "hookpress_dev_secret")
    s3_bucket_media: str = os.getenv("S3_BUCKET_MEDIA", "hookpress-media")
    s3_use_ssl: bool = os.getenv("S3_USE_SSL", "false").lower() == "true"

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "")


settings = WorkerSettings()
