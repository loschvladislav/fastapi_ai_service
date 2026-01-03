from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str

    # Database
    db_user: str = "ai_service"
    db_password: str = "ai_service_pass"
    db_name: str = "ai_service_db"
    db_host: str = "localhost"
    db_port: int = 5436

    # Rate Limiting
    rate_limit_per_minute: int = 10

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


settings = Settings()
