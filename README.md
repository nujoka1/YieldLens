# YieldLens Nigeria

## Status and Windows setup

Publication checks (18 September): Compose/Ruff passed; the latest unit attempt had **8 passed, 2 subprocess-deadline failures, 1 integration skip, 34% coverage** on host Python 3.14.6. See [publication verification](docs/publication-verification.md). This is source availability, not a successful runtime release.

The Phase 1 source and bounded Phase 1.5 probes are included. **Full-stack validation remains incomplete; Windows runtime is not yet verified.**

Windows users: follow [Windows setup with WSL2 and Docker Desktop](docs/windows-setup.md). It covers PowerShell installation, Ubuntu commands, private credentials, readiness, tests and safe shutdown. Do not run the full stack on a machine that freezes or has storage errors.

Historical 6 September results: 9 unit tests passed, 1 integration test skipped, 46% host coverage. Kafka startup instability and the Spark/end-to-end result remain unresolved. See [runtime evidence](docs/runtime-verification.md); no real datasets, models or dashboard are implemented.

YieldLens Nigeria is a bean/cowpea yield and climate/soil-risk project. Phase 1.5 provides a local infrastructure foundation and bounded synthetic integration probes. Agricultural acquisition, the 25,920,000-event simulator, models, scalability experiments and dashboard remain deferred.

The target architecture is:

`Sources → Python/Kafka → MinIO/Parquet → Spark/PySpark → Spark MLlib → PostgreSQL → Streamlit/Plotly`

Kafka, MinIO and Spark are the three substantive big-data technologies. See [architecture decisions](docs/architecture/decisions.md) and [runtime verification](docs/runtime-verification.md).

## Prerequisites and configuration

Install Docker Engine/Compose v2+ and GNU Make. Python 3.12 is the supported application version; the app image includes the pinned development test tools. A host Python environment is needed for the Docker integration-test orchestrator.

On a fresh checkout:

```bash
python3 scripts/init_env.py
make setup PYTHON=python3.12
docker compose config --quiet
make pull
make up
```

The initializer creates random local credentials with file mode 0600 and refuses to overwrite an existing `.env`. Existing users must preserve their file. `make setup` also preserves it. No credentials need to be printed. PostgreSQL stores its role password in its persistent database: changing `.env` does not update that role automatically.

`make up` builds the development image and starts PostgreSQL, MinIO, Kafka, Spark master, Spark worker and app sequentially, waiting for readiness at each step. It preserves named volumes. The topic, bucket and shared-test-directory initializers must exit successfully.

## Local endpoints

All published ports bind to **127.0.0.1**.

| Service | Endpoint |
|---|---|
| Kafka host client | localhost:29092 (Docker clients use kafka:9092) |
| MinIO API | http://127.0.0.1:9000 |
| MinIO console | http://127.0.0.1:19001 |
| Spark master UI | http://127.0.0.1:8080 |
| Spark master RPC | spark://localhost:7077 |
| Spark worker UI | http://127.0.0.1:8081 |
| PostgreSQL | localhost:5432 |

`MINIO_CONSOLE_PORT` can override 19001. Port 9001 on the validation host is already owned by the unrelated `mqtt-broker` container; it was preserved.

## Checks and shutdown

```bash
docker compose ps -a
docker compose exec -T app python -m yieldlens.healthcheck
curl --fail http://127.0.0.1:9000/minio/health/ready
curl --fail http://127.0.0.1:8080/json/
make lint
make integration
make coverage
docker stats --no-stream
free -m
docker compose logs --tail=50 kafka minio postgres spark-master spark-worker app
docker compose stop
# Alternatively, remove containers/network while retaining every named volume:
make down
```

`make integration` runs the complete host suite, including the real Docker probe. It refuses to publish a test record until all six services are healthy. `make test` runs unit tests and explicitly skips the opt-in Docker probe. `make coverage` runs Python 3.12 tests and readiness inside the app, combines them with instrumented real smoke operations, and exports an HTML report to ignored `htmlcov/`. Run integration before coverage; reports do not measure JVM/Spark source coverage.

The app health check performs actual Kafka metadata, authenticated MinIO/PostgreSQL, and registered Spark worker checks. PostgreSQL's own `pg_isready` is only a readiness signal; the app and integration checks provide the authentication evidence.

## Resource-constrained development profile

| Component | Runtime allocation | Container memory ceiling |
|---|---|---|
| Kafka | 128 MiB initial / 256 MiB maximum JVM heap | 512 MiB |
| Kafka initializer | 32–128 MiB JVM heap | 256 MiB |
| MinIO | Go memory target 192 MiB | 384 MiB |
| MinIO initializer | one-shot | 256 MiB |
| Spark master | 128 MiB daemon heap; smoke driver 512 MiB | 1 GiB |
| Spark worker | 128 MiB daemon heap; one core / 512 MiB executor capacity | 1 GiB |
| PostgreSQL | 16 MiB shared buffers, 1 MiB work memory, 20 connections | 192 MiB |
| Python app | development runtime and checks | 192 MiB |

Heap/capacity settings do not include all native, Python or operating-system memory. Both driver and executor use 512 MiB for the smoke test. Automatic restarts are disabled so failures remain visible. Do not kill unrelated processes, create swap, or change system-wide settings to make the checks pass.

## Data and cleanup boundaries

MinIO uses `yieldlens-raw` plus `yieldlens-curated/{bronze,silver,gold,checkpoints}/`. Small `.keep` marker objects define the virtual prefixes. The smoke test uses a unique `_smoke/<uuid>/synthetic.json` raw object, checks SHA-256, and removes that object afterward. Spark Parquet files live temporarily in the dedicated shared `smoke-data` volume. PostgreSQL uses a session-local temporary table and deletes the test row. Synthetic Kafka messages remain subject to normal Kafka retention; deleting a topic or volume is never part of cleanup.

The tiny smoke job fetches a signed raw object in the Spark driver and creates a distributed DataFrame, writes/reads shared Parquet, and returns an aggregate that Python writes to PostgreSQL. Native distributed S3A access and Spark JDBC writes are future integration work. This small-object bridge is not intended for bulk ingestion.

## Troubleshooting

- Port conflict: inspect `docker ps --format '{{.Names}} {{.Ports}}'` and `ss -ltn`; change the local published port, never terminate an unrelated service.
- Unhealthy service: inspect `docker compose ps -a`, its logs, and `docker inspect yieldlens-app-1 --format '{{json .State.Health}}'`. Avoid unrestricted `docker inspect` or rendered Compose output: they can expose environment credentials.
- Database authentication failure after changing configuration: reconcile the existing local database role credential through an authenticated administrative session. Do not delete the volume or assume a restart rotates passwords.
- Spark worker missing: inspect worker logs and master `/json/`; verify the reported 512 MiB capacity and registration before submitting a job.
- Memory pressure: sample `free -m` and `docker stats --no-stream`; inspect OOM flags. Stop the affected YieldLens validation if limits cannot be respected.
- Moved checkout: use `.venv/bin/python -m pytest` and `.venv/bin/python -m ruff`; old console-script launchers may contain the previous absolute path. Recreate the local environment with Python 3.12 when convenient.

This is a single-host development topology with plaintext internal traffic and single-copy Kafka/object storage. It is not a production-readiness or scalability claim. See [Phase 1 status](docs/phase-1.md) for measured verification boundaries.
