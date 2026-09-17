# YieldLens Nigeria

A big-data project for bean/cowpea yield forecasting and climate/soil-risk assessment in Nigeria, designed for academic research and future commercial extension.

## Current status

Updated **17 September 2026**; latest recorded validation **6 September 2026**. Results below are historical, not a new runtime check.

**Phase 1 scaffolding is implemented locally. Phase 1.5 is partial; Phase 2 ingestion remains blocked.** This GitHub repository currently contains the overview and license, not the local implementation described here.

## Planned architecture

```text
NASA POWER / ISRIC SoilGrids / FAOSTAT / synthetic IoT
 -> Python + Kafka -> MinIO + Parquet -> Spark / PySpark
 -> Spark MLlib -> PostgreSQL -> Streamlit / Plotly
```

Kafka, MinIO and Spark are the three substantive big-data technologies. Planned synthetic workload: 200 farms, one event per minute for 90 days (**25,920,000 records**). This workload has not been generated or benchmarked.

## Implemented locally

- Repository scaffold, centralized configuration, structured logging, tests, documentation and development commands.
- Docker Compose: Kafka 3.9.1 in KRaft mode, MinIO, Spark 3.5.6 master/worker, PostgreSQL 17.6 and Python 3.12 development environment.
- Persistent volumes, readiness checks, localhost-only published ports and conservative development memory limits.
- Ignored secrets and runtime artifacts; local environment-file mode verified as 0600 during validation.
- Bounded, explicitly synthetic infrastructure probes; no agricultural datasets downloaded.

## Verification evidence

| Check | Recorded result |
|---|---|
| Compose validation and Ruff lint/format | Passed on latest recorded attempt |
| Unit suite | 9 passed, 1 opt-in integration test skipped |
| Host Python coverage | 46%; not end-to-end coverage |
| Kafka KRaft and exact message round trip | Passed earlier; latest startup was unstable |
| Versioned telemetry/climate/FAOSTAT topics | Earlier verification: 6 partitions and replication factor 1 each |
| MinIO API/console, storage zones and checksum round trip | Passed earlier |
| PostgreSQL authentication, schemas and temporary-table transaction | Passed independently earlier |
| Spark worker registration | Passed earlier |
| Spark Parquet and complete synthetic aggregate path | **Not verified** |

Earlier component passes are not a successful full-stack run. On 5 September, Kafka was confirmed OOM-killed at its 512 MiB container ceiling during a quorum probe. On 6 September, Kafka unexpectedly exited and was restarted during startup; that exit's cause remains unresolved and was **not confirmed as OOM**. Host I/O contention was observed but does not establish causation.

Validation stopped with project containers shut down and named volumes preserved. No unrelated processes were terminated, swap added, or system-wide settings changed by the validation workflow.

## Next milestone

Diagnose Kafka's exit and dependency-restart behavior, establish stable readiness within approved resource limits, then verify the synthetic Kafka -> MinIO -> Spark Parquet -> PostgreSQL aggregate path. Phase 2 requires successful Phase 1.5 review and approval.

Real dataset ingestion, the full simulator, forecasting models, risk engine, scalability experiments and dashboard are **not implemented**. No model accuracy, performance or production-readiness claims are made.
