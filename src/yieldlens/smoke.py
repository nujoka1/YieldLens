"""Bounded synthetic probes for real infrastructure."""

import hashlib
import io
import json
import sys
import uuid
from datetime import timedelta

import psycopg
from kafka import KafkaConsumer, KafkaProducer, TopicPartition
from kafka.admin import KafkaAdminClient
from minio import Minio

from yieldlens.config import get_settings


def object_store():
    s = get_settings()
    return Minio(
        s.MINIO_ENDPOINT,
        access_key=s.MINIO_ACCESS_KEY,
        secret_key=s.MINIO_SECRET_KEY.get_secret_value(),
        secure=s.MINIO_SECURE,
    )


def database():
    s = get_settings()
    return psycopg.connect(
        host=s.POSTGRES_HOST,
        port=s.POSTGRES_PORT,
        dbname=s.POSTGRES_DB,
        user=s.POSTGRES_USER,
        password=s.POSTGRES_PASSWORD.get_secret_value(),
        connect_timeout=10,
    )


def prepare():
    s = get_settings()
    run_id = uuid.uuid4().hex
    record = {
        "synthetic": True,
        "purpose": "infrastructure_smoke",
        "run_id": run_id,
        "farm_id": "synthetic-smoke-farm",
        "soil_moisture": 42.0,
    }
    payload = json.dumps(record, sort_keys=True).encode()
    admin = KafkaAdminClient(bootstrap_servers=s.KAFKA_BOOTSTRAP_SERVERS)
    try:
        metadata = admin.describe_topics(
            [s.KAFKA_TOPIC_IOT, s.KAFKA_TOPIC_CLIMATE, s.KAFKA_TOPIC_FAOSTAT]
        )
        topics = []
        for topic in metadata:
            if topic["error_code"]:
                raise RuntimeError("Required Kafka topic unavailable")
            topics.append(
                {
                    "topic": topic["topic"],
                    "partitions": len(topic["partitions"]),
                    "replication_factor": len(topic["partitions"][0]["replicas"]),
                }
            )
    finally:
        admin.close()
    producer = KafkaProducer(
        bootstrap_servers=s.KAFKA_BOOTSTRAP_SERVERS, acks="all", retries=3, request_timeout_ms=15000
    )
    try:
        sent = producer.send(s.KAFKA_TOPIC_IOT, key=run_id.encode(), value=payload).get(timeout=30)
    finally:
        producer.close(timeout=10)
    consumer = KafkaConsumer(
        bootstrap_servers=s.KAFKA_BOOTSTRAP_SERVERS,
        enable_auto_commit=False,
        consumer_timeout_ms=15000,
    )
    try:
        partition = TopicPartition(sent.topic, sent.partition)
        consumer.assign([partition])
        consumer.seek(partition, sent.offset)
        received = next(consumer)
        if received.value != payload or received.key != run_id.encode():
            raise AssertionError("Kafka message round-trip mismatch")
    finally:
        consumer.close()
    client = object_store()
    for bucket in (s.MINIO_RAW_BUCKET, s.MINIO_CURATED_BUCKET):
        if not client.bucket_exists(bucket):
            raise AssertionError("Required bucket missing")
    for zone in ("bronze", "silver", "gold", "checkpoints"):
        client.stat_object(s.MINIO_CURATED_BUCKET, f"{zone}/.keep")
    key = f"_smoke/{run_id}/synthetic.json"
    client.put_object(
        s.MINIO_RAW_BUCKET,
        key,
        io.BytesIO(payload),
        len(payload),
        content_type="application/json",
        metadata={"synthetic": "true"},
    )
    try:
        response = client.get_object(s.MINIO_RAW_BUCKET, key)
        try:
            readback = response.read()
        finally:
            response.close()
            response.release_conn()
        digest = hashlib.sha256(payload).hexdigest()
        if hashlib.sha256(readback).hexdigest() != digest:
            raise AssertionError("MinIO checksum mismatch")
        return {
            "run_id": run_id,
            "object_key": key,
            "sha256": digest,
            "topics": topics,
            "url": client.presigned_get_object(
                s.MINIO_RAW_BUCKET, key, expires=timedelta(minutes=10)
            ),
        }
    except BaseException:
        client.remove_object(s.MINIO_RAW_BUCKET, key)
        raise


def postgres_probe(result):
    if result.get("synthetic") is not True or result.get("mean_moisture") != 42.0:
        raise ValueError("Unexpected synthetic aggregate")
    with database() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name IN ('analytics', 'metadata')"
        )
        if {row[0] for row in cur.fetchall()} != {"analytics", "metadata"}:
            raise AssertionError("Required PostgreSQL schemas missing")
        cur.execute(
            "CREATE TEMP TABLE smoke_aggregate "
            "(synthetic boolean, value double precision) ON COMMIT DROP"
        )
        cur.execute("INSERT INTO smoke_aggregate VALUES (%s, %s)", (True, result["mean_moisture"]))
        cur.execute("SELECT synthetic, value FROM smoke_aggregate")
        if cur.fetchone() != (True, 42.0):
            raise AssertionError("PostgreSQL aggregate round-trip failed")
        cur.execute("DELETE FROM smoke_aggregate")
        cur.execute("SELECT count(*) FROM smoke_aggregate")
        if cur.fetchone()[0] != 0:
            raise AssertionError("Temporary row deletion failed")
    return {"postgres": "passed", "synthetic": True, "mean_moisture": 42.0}


def main():
    operation = sys.argv[1]
    if operation == "prepare":
        result = prepare()
    elif operation == "postgres":
        result = postgres_probe(json.load(sys.stdin))
    elif operation == "cleanup":
        run_id = uuid.UUID(json.load(sys.stdin)["run_id"]).hex
        s = get_settings()
        object_store().remove_object(s.MINIO_RAW_BUCKET, f"_smoke/{run_id}/synthetic.json")
        result = {"cleanup": "passed"}
    else:
        raise ValueError("Unknown smoke operation")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
