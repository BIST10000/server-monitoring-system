from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    project_name: str = Field(default="server-monitoring-system", alias="PROJECT_NAME")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8080, alias="API_PORT")
    api_root_path: str = Field(default="", alias="API_ROOT_PATH")

    api_key_header: str = Field(default="X-Api-Key", alias="API_KEY_HEADER")
    api_keys: str = Field(default="dev-key-1", alias="API_KEYS")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="monitoring", alias="POSTGRES_DB")
    postgres_user: str = Field(default="monitoring", alias="POSTGRES_USER")
    postgres_password: str = Field(default="monitoring", alias="POSTGRES_PASSWORD")

    metric_retention_days: int = Field(default=30, alias="METRIC_RETENTION_DAYS")
    heartbeat_stale_seconds: int = Field(default=120, alias="HEARTBEAT_STALE_SECONDS")

    ui_enabled: bool = Field(default=True, alias="UI_ENABLED")
    ui_require_api_key: bool = Field(default=False, alias="UI_REQUIRE_API_KEY")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def api_key_set(self) -> set[str]:
        return {k.strip() for k in self.api_keys.split(",") if k.strip()}


settings = Settings()

