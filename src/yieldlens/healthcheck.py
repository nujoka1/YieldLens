"""Real service readiness; no secret or payload logging."""

import json
from urllib.request import urlopen

from kafka.admin import KafkaAdminClient

from yieldlens.config import get_settings
from yieldlens.smoke import database, object_store


def main():
    settings = get_settings()
    admin = KafkaAdminClient(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        request_timeout_ms=5000,
        api_version_auto_timeout_ms=5000,
    )
    try:
        if settings.KAFKA_TOPIC_IOT not in admin.list_topics():
            raise RuntimeError("IoT topic unavailable")
    finally:
        admin.close()
    if not object_store().bucket_exists(settings.MINIO_RAW_BUCKET):
        raise RuntimeError("Raw bucket unavailable")
    with database() as connection:
        if connection.execute("SELECT 1").fetchone() != (1,):
            raise RuntimeError("Database readiness failed")
    with urlopen("http://spark-master:8080/json/", timeout=5) as response:
        master = json.load(response)
    if not any(worker["state"] == "ALIVE" for worker in master["workers"]):
        raise RuntimeError("No registered Spark worker")


if __name__ == "__main__":
    main()
