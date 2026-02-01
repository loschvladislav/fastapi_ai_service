from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # AI Provider
    ai_provider: str = "openai"
    openai_api_key: str

    # Database
    db_user: str = "ai_service"
    db_password: str = "ai_service_pass"
    db_name: str = "ai_service_db"
    db_host: str = "localhost"
    db_port: int = 5436

    # Test Database
    test_db_name: str = "ai_service_test_db"

    # Rate Limiting
    rate_limit_per_minute: int = 10

    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600  # 1 hour

    # App
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        """Async database URL for SQLAlchemy."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_sync(self) -> str:
        """Sync database URL for Alembic migrations."""
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def test_database_url(self) -> str:
        """Async database URL for tests (separate database)."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.test_db_name}"


settings = Settings()
