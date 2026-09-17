# Phase 1 Architecture Decisions

## Kafka with KRaft

Kafka decouples high-velocity producers from storage consumers and supports partitioned processing, replay, and back-pressure. KRaft avoids a separate ZooKeeper dependency. The local single broker is appropriate for development but has no broker redundancy. Later partition keys should preserve ordering per farm while distributing 200 farms across partitions.

## MinIO and Parquet

MinIO supplies an S3-compatible object-store boundary that can move to managed object storage without redesigning every job. Parquet provides columnar compression, predicate pushdown, and efficient Spark scans. The immutable raw bucket is separated from curated outputs to reduce accidental overwrite and clarify provenance.

## Spark standalone

Spark is the distributed engine for cleaning, joins, feature engineering, scalability experiments, and later MLlib work. A master plus worker demonstrates the execution boundary locally. Production scaling should add workers/executors and externalize orchestration rather than treating this Compose file as a production cluster.

## PostgreSQL serving layer

PostgreSQL is reserved for small, query-oriented aggregates, forecasts, risk results, and pipeline metadata. Loading the complete telemetry lake into it would duplicate MinIO and weaken the intended lake/compute architecture.

## Python application

Python owns API acquisition and Kafka producer/consumer orchestration in later phases. Phase 1 includes only configuration, structured logging, lifecycle behavior, and a local health check; it intentionally contains no fake connectors.

## Persistence and initialization

Named Docker volumes retain broker, object-store, database, and Spark working data across ordinary shutdowns. One-shot initializer containers create topics and buckets idempotently. PostgreSQL init SQL runs only for a new database volume, matching the upstream image contract.

## Security boundary

Phase 1 is a localhost development environment. Services use plaintext internal protocols and expose ports for inspection. Placeholder passwords exist only to make configuration explicit and must be changed. A production design must add TLS, authentication/authorization, restricted port exposure, secret management, backups, audit logging, and multiple failure domains.
