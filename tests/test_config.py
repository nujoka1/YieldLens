import pytest
from pydantic import ValidationError

from yieldlens.config import Settings


def test_defaults_describe_compose_network() -> None:
    settings = Settings(_env_file=None)

    assert settings.KAFKA_BOOTSTRAP_SERVERS == "kafka:9092"
    assert settings.MINIO_ENDPOINT == "minio:9000"
    assert settings.SPARK_MASTER_URL == "spark://spark-master:7077"
    assert settings.POSTGRES_HOST == "postgres"


def test_secret_values_are_masked() -> None:
    rendered = repr(Settings(_env_file=None))

    assert "change-me-postgres-password" not in rendered
    assert "change-me-minio-password" not in rendered


def test_production_rejects_placeholder_credentials() -> None:
    settings = Settings(
        YIELDLENS_ENV="production",
        MINIO_SECRET_KEY="change-me-minio-password",
        POSTGRES_PASSWORD="change-me-postgres-password",
        _env_file=None,
    )

    with pytest.raises(ValueError, match="placeholder credentials"):
        settings.assert_safe_for_production()


def test_blank_endpoint_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must not be blank"):
        Settings(KAFKA_BOOTSTRAP_SERVERS=" ", _env_file=None)
