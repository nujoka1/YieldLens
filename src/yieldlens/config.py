"""Typed, centralized application configuration."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    YIELDLENS_ENV: Literal["development", "test", "production"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC_IOT: str = "yieldlens.iot.telemetry.v1"
    KAFKA_TOPIC_CLIMATE: str = "yieldlens.climate.daily.v1"
    KAFKA_TOPIC_FAOSTAT: str = "yieldlens.faostat.annual.v1"

    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_SECURE: bool = False
    MINIO_ACCESS_KEY: str = "yieldlens_admin"
    MINIO_SECRET_KEY: SecretStr = SecretStr("change-me-minio-password")
    MINIO_RAW_BUCKET: str = "yieldlens-raw"
    MINIO_CURATED_BUCKET: str = "yieldlens-curated"

    POSTGRES_DB: str = "yieldlens"
    POSTGRES_USER: str = "yieldlens_app"
    POSTGRES_PASSWORD: SecretStr = SecretStr("change-me-postgres-password")
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = Field(default=5432, ge=1, le=65535)

    SPARK_MASTER_URL: str = "spark://spark-master:7077"

    @field_validator(
        "KAFKA_BOOTSTRAP_SERVERS",
        "MINIO_ENDPOINT",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_HOST",
        "MINIO_RAW_BUCKET",
        "MINIO_CURATED_BUCKET",
    )
    @classmethod
    def value_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("configuration value must not be blank")
        return value

    def assert_safe_for_production(self) -> None:
        """Reject documented development credentials in production mode."""
        if self.YIELDLENS_ENV != "production":
            return
        placeholders = {
            self.MINIO_SECRET_KEY.get_secret_value(),
            self.POSTGRES_PASSWORD.get_secret_value(),
        }
        if any(value.startswith("change-me-") for value in placeholders):
            raise ValueError("placeholder credentials are forbidden in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.assert_safe_for_production()
    return settings
