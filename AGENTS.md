# YieldLens Nigeria Engineering Rules

## Scope and product boundary

YieldLens Nigeria is an academic big-data platform designed for commercial extension. Treat all outputs as agricultural decision support, not guaranteed agronomic advice. Never fabricate source data, experiment results, benchmark measurements, model metrics, or deployment status.

The approved pipeline is:

`NASA POWER / SoilGrids / FAOSTAT / synthetic IoT -> Python + Kafka -> MinIO + Parquet -> Spark/PySpark -> Spark MLlib -> PostgreSQL -> Streamlit + Plotly`

Kafka, MinIO, and Spark are the three substantive big-data technologies. Do not replace them without an explicit architecture decision.

## Phase boundaries

- Phase 1 establishes the repository, local infrastructure, configuration, logging, tests, and documentation.
- Phase 1.5 permits bounded synthetic infrastructure probes and temporary database tables.
- Use conservative local memory limits and sequential startup; never kill unrelated processes, add swap, or delete volumes.
- Do not implement dataset acquisition, synthetic event generation, ETL, modeling, or the dashboard during Phase 1.
- Later phases must use real API responses or clearly labelled synthetic records and retain provenance.

## Data architecture

- Kafka topic names are versioned and centrally configured.
- MinIO is the system of record for immutable raw data and curated Parquet datasets.
- Use `raw/bronze/silver/gold` semantics documented in `docs/architecture/data-lifecycle.md`.
- PostgreSQL contains serving-layer aggregates and operational metadata, not the full 25,920,000-event lake.
- Preserve raw records; transformations produce new objects and must be reproducible.
- Partition IoT Parquet by event date and an intentionally chosen farm bucket; verify partition sizes before finalizing.

## Engineering rules

- Read this file and relevant documentation before edits.
- Inspect `git status`; preserve unrelated user work.
- Keep secrets in `.env` or an external secret manager. Never commit `.env`, credentials, downloaded datasets, generated Parquet, or production records.
- Centralize runtime settings in `yieldlens.config`; do not scatter hostnames or credentials through code.
- Emit structured logs with event names and useful identifiers; never log secrets or full sensitive payloads.
- Validate schemas at ingestion boundaries and use UTC timestamps.
- Make writes retry-safe and idempotent. Define Kafka keys deliberately to retain per-farm ordering where required.
- Add behavior-focused tests for every implemented component.
- Run `make check` before handoff and report failures honestly.
- Do not call a Compose parse, unit test, or synthetic run a scalability result. Benchmark claims require the controlled 25/50/100 percent experiment.

## Git and review discipline

- Keep changes phase-focused and reviewable.
- Do not commit, push, deploy, destroy volumes, or download bulk datasets unless explicitly requested.
- Review diffs for secret exposure, fake results, dead paths, and incomplete interactions.
