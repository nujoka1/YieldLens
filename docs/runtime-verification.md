# Phase 1.5 runtime verification

## Current rerun — 2026-09-06: BLOCKED before integration

This entry supersedes all earlier "latest" results below. Configuration and memory limits were unchanged. Commands: `make validate lint && make up`, read-only Docker inspect/stats/logs/events, `free -m`, `cat /proc/pressure/io`, then termination of this run's identified startup processes and `timeout 120 docker compose stop -t 20`, followed by `make test` and `git diff --check`.

Compose validation and Ruff lint/format passed. The app image built successfully using cached dependencies. PostgreSQL, MinIO, Kafka and both Spark services each reached healthy state during sequential startup, but the app never became ready. Kafka unexpectedly exited during startup and Compose started it again while resolving app dependencies. Inspection showed a prior finish at 17:21:13.170207141Z and new start at 17:22:40.404933294Z. Kafka then logged recovery without a clean-shutdown file. The retained Docker event query returned no matching exit/OOM events; the cause of that earlier exit remains unresolved. A diagnostic approval timed out once; its permitted retry succeeded.

Startup was aborted because stable readiness was not established. No integration test or new synthetic probe record was created. Kafka roundtrip, MinIO checksum, Spark Parquet, PostgreSQL transaction and end-to-end aggregate were **NOT RUN in this attempt**; older independent results are historical only. Worker health does not substitute for a fresh master-registration integration check.

Host RAM: 7826 MiB total; 1485 MiB available before startup, 831 MiB at a later startup sample, 1763 MiB after shutdown. Swap remained zero. A full-I/O-pressure sample reported avg10=73.86%, avg60=66.94%, avg300=50.01%; contention was observed, but is not a proven cause of Kafka's exit.

Observed container samples (not peaks): Kafka 309.8/512 MiB, MinIO 246.2/384 MiB, Spark master 232/1024 MiB, Spark worker 215.8/1024 MiB, PostgreSQL 11.43/192 MiB. App did not start, so there is no app usage sample.

Final status: all YieldLens services stopped; all six final OOM flags false. Kafka exited 137 during the bounded shutdown (this exit code alone does not establish OOM); Spark master/worker exited 143; MinIO/PostgreSQL/app exited 0. Named volumes and unrelated mqtt-broker were preserved. No swap, system settings, credentials or limits were changed. The existing .env was verified ignored and mode 0600; secret values were not printed.

Unit suite: **9 passed, 1 skipped in 5.25 seconds**, Python 3.14.6. Integration was explicitly skipped because dependencies were not ready. Current host coverage: **46% (188 statements, 101 missed)**, in ignored htmlcov/index.html. This replaces the preceding 34% report. Git whitespace checks passed.

**Phase 1.5 remains incomplete; Phase 2 is not ready.** Further work should diagnose the unexpected broker exit and startup's dependency-restart behavior before another attempt. No production-readiness claim is made.

## Latest rerun — FAILED (2026-09-05 UTC)

This section supersedes the historical results below. All six services reached healthy status after sequential startup, but Kafka was then OOM-killed during its in-container metadata-quorum CLI probe, before preparing any new synthetic record or launching Spark.

Docker evidence: OOMKilled=true, exit code 137, memory ceiling 536870912 bytes (512 MiB), FinishedAt=2026-09-05T19:42:18.212374127Z. The broker heap was capped at 256 MiB; the additional quorum JVM used 32–64 MiB heap. Heap limits do not cover total container memory.

The full suite returned **8 passed, 2 failed in 69.04 seconds**. Failures: quorum inspection (exit 137, no output) and the runtime lifecycle test's 15-second readiness deadline. Current host coverage: **34% (188 statements, 125 missed)**, exported to ignored htmlcov/index.html. The earlier 79% report below is historical, not current coverage. Ruff lint/format, Compose validation and Git whitespace checks passed.

Commands executed for this rerun:

```bash
make up
make lint
docker compose config --quiet
git diff --check
docker compose exec -T app python -m coverage erase && make integration
docker compose exec -T -e 'KAFKA_HEAP_OPTS=-Xms32m -Xmx64m' kafka /opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka:9092 describe --status
timeout 120 docker compose stop -t 20
```

The quorum command shown above was invoked by the integration test, not a subsequent retry. Read-only diagnostics included Docker status/stats and selected inspect fields, free -m, /proc/pressure/io and Spark cgroup memory.events.

RAM total: 7826 MiB. Available: 2309 MiB before startup, 1021 MiB during testing, 2318 MiB after shutdown. Swap: zero. Last observed container samples (not peaks):

| Container | Usage / ceiling |
|---|---|
| Kafka | 487.5 / 512 MiB |
| MinIO | 265.9 / 384 MiB |
| Spark master | 234.1 / 1024 MiB |
| Spark worker | 201.5 / 1024 MiB |
| PostgreSQL | 15.82 / 192 MiB |
| Python app | 29.76 / 192 MiB |

Both Spark cgroup memory-event sets were zero, including oom/oom_kill. Kafka had already exited, so its cgroup counters could not be read through exec. All five other long-running containers reported OOMKilled=false.

All YieldLens services were stopped: Kafka exit 137; Spark master/worker exit 143 after intentional stop signals; app, MinIO and PostgreSQL exit 0; initializers exit 0. Named volumes were preserved. No unrelated processes were terminated, no swap/system settings changed and no limits raised. .env remained ignored and mode 0600; generated data, logs and coverage artifacts remain excluded from Git.

No new synthetic Kafka message, MinIO object, request file or Spark job was created by this rerun. Earlier independent Kafka/MinIO/PostgreSQL checks below are not rerun passes. Spark Parquet and the end-to-end aggregate remain **NOT VERIFIED; Phase 2 is blocked**.

This confirms a Kafka container-ceiling failure, not exhaustion of all host RAM. A possible next approved correction is to isolate administrative JVMs in a separately capped helper before another controlled rerun. That correction has not been implemented or validated.

## Historical attempt — results below predate the failed rerun

The earlier no-OOM statements, 79% coverage and shutdown exit codes below describe only the preceding attempt.

## Outcome

**PARTIAL — not ready for Phase 2.** All services became healthy under conservative limits, but the Spark Parquet and complete end-to-end checks did not complete. Their repaired runner remains unverified. Validation stopped under the user's controlled-resource constraint.

Date: 2026-09-05. Existing repository changes were inspected; no commits or pushes were made.

## Service and integration evidence

| Check | Observed result |
|---|---|
| Docker image pull | Required Kafka, MinIO server/client, Spark and PostgreSQL images pulled successfully |
| Python development image | Built successfully with Python 3.12.7 and development/coverage dependencies |
| Kafka KRaft | Metadata-quorum status returned a leader; broker logs identify KafkaRaftServer |
| Kafka persistence | Effective server setting: `log.dirs=/var/lib/kafka/data`; mounted `kafka-data` volume |
| Kafka topics | Required versioned topics verified; each has 6 partitions and replication factor 1 |
| Kafka produce/consume | Exact synthetic key/value read back at the produced partition/offset |
| MinIO API and console | HTTP 200; API localhost:9000, console localhost:19001 |
| MinIO zones | `yieldlens-raw`; `yieldlens-curated/bronze/`, `silver/`, `gold/`, `checkpoints/` verified |
| MinIO write/read | 158-byte synthetic JSON object uploaded and read back; SHA-256 equality verified |
| MinIO cleanup | Original cleanup timed out; subsequent exact-key cleanup succeeded and NoSuchKey confirmed |
| Spark registration | Master detected ALIVE worker; worker log reports 1 core and 512 MiB |
| Spark submit / Parquet | FAIL: host command exceeded 240 seconds; no row-count/schema result obtained |
| PostgreSQL connectivity | Actual authenticated connection and SELECT 1 passed after credential reconciliation |
| PostgreSQL schemas | analytics and metadata verified |
| PostgreSQL safe transaction | Independent temporary table: insert synthetic value 42.0, select equality, delete, count zero; table removed on commit |
| End-to-end aggregate | FAIL / NOT VERIFIED: Spark-derived value was never obtained or persisted |
| Temporary Spark files | Read-only inspection of dedicated smoke volume found no files |
| OOM checks | All six long-running containers reported OOMKilled=false before and after controlled stops |

The PostgreSQL test above is an independent test with an explicitly synthetic input. It is **not** presented as a completed Spark-to-PostgreSQL result.

Kafka topics:

| Topic | Partitions | Replication factor |
|---|---:|---:|
| yieldlens.iot.telemetry.v1 | 6 | 1 |
| yieldlens.climate.daily.v1 | 6 | 1 |
| yieldlens.faostat.annual.v1 | 6 | 1 |

Temporary raw object removed: `_smoke/c128338565664a8bbadffefe3e413ba7/synthetic.json`.
No topics or existing volumes were deleted. Synthetic Kafka records remain under broker retention.

## Failures and fixes

1. Host port 9001 was occupied by the unrelated `mqtt-broker` container, image `eclipse-mosquitto`, observed host PID 2175. It was not terminated. MinIO console moved to configurable localhost:19001.
2. Spark master bound its container address; the original localhost:7077 TCP health probe failed. The probe now uses the Spark service address.
3. Kafka's CLI health probe exceeded its old 10-second deadline. It now uses a small 64 MiB CLI heap, a 45-second deadline and a 60-second interval; the broker heap is capped at 256 MiB.
4. Actual PostgreSQL authentication failed even though pg_isready passed. App and server environment credentials matched, but the persisted role credential did not authenticate. The existing local role was reconciled to the configured secret without deleting/reinitializing the volume or altering application schemas. App readiness then passed.
5. The original Spark probe used `json.load(sys.stdin)` under spark-submit. Spark's PythonRunner does not forward launcher input to the Python child. Source evidence: [Spark 3.5.6 PythonRunner](https://github.com/apache/spark/blob/v3.5.6/core/src/main/scala/org/apache/spark/deploy/PythonRunner.scala). The harness now writes a private UUID-named request file, passes only its path, and attempts removal in cleanup. An in-container 180-second timeout bounds future jobs. **This repaired route has not been runtime verified.**
6. The full integration command timed out at 240 seconds; cleanup also timed out. A concurrent host lifecycle unit test missed its 15-second readiness deadline. That unit test passed after Spark was stopped. Both failures remain recorded.
7. Host I/O pressure was severe: one sample showed full I/O pressure avg300=76.76%, and another avg300=74.23%. This is observed host contention, not proof that insufficient RAM caused the Spark hang. No OOM was observed; the stdin defect independently explains a blocking path.

The complete integration suite was not rerun after these failures. Deadlines were not relaxed to manufacture a pass.

## Resource record

Total RAM: 7,826 MiB (about 7.6 GiB). Swap: 0 throughout.

| Observation | Available RAM |
|---|---:|
| Resumed inspection before controlled restart | approximately 1.4 GiB |
| PostgreSQL started alone | 2,434 MiB |
| PostgreSQL + MinIO | 2,206 MiB |
| Plus Kafka | 1,840 MiB |
| Plus Spark master | 1,543 MiB |
| Plus Spark worker | 1,327 MiB |
| All services healthy | 1,220 MiB |
| During validation | 1,124 MiB; later 1,114 MiB |
| Spark stopped | 1,734 MiB |
| All YieldLens services stopped | 2,338 MiB |

Observed samples (not measured peaks):

| Container | Before submission | Later sample | Configured ceiling |
|---|---:|---:|---:|
| Kafka | 431.2 MiB | 385.1 MiB | 512 MiB |
| MinIO | 238.7 MiB | 263.8 MiB | 384 MiB |
| PostgreSQL | 13.63 MiB | 13.84 MiB | 192 MiB |
| Spark master | 236.4 MiB | 433.9 MiB | 1 GiB |
| Spark worker | 211.9 MiB | 215.4 MiB | 1 GiB |
| Python app | 46.19 MiB | 31.54 MiB | 192 MiB |

Worker capacity: 512 MiB / 1 core. Smoke driver and executor: 512 MiB each. Spark daemon heaps: 128 MiB each. PostgreSQL: shared_buffers 16 MiB, work_mem 1 MiB, max_connections 20. MinIO Go memory target: 192 MiB. These settings do not equal total process RSS.

No unrelated processes were killed, no swap was created, and no system-wide configuration was changed. Session-local PostgreSQL logging settings were used only to avoid exposing credentials during the local password reconciliation.

## Commands executed

Main commands and outcomes (password-bearing inspection output was never printed):

```bash
docker compose pull
docker compose build app
docker compose config --quiet
# Initial startup failed on port 9001; subsequent attempts exposed the health/auth issues.
docker compose up --build -d --wait --wait-timeout 180
# Controlled restart after applying limits:
docker compose stop app spark-worker spark-master kafka minio postgres
for service in postgres minio kafka spark-master spark-worker app; do
  docker compose up -d --wait --wait-timeout 300 "$service" || break
  docker stats --no-stream --format '{{.Name}} {{.MemUsage}}'
  free -m
done
docker compose exec -T app python -m yieldlens.healthcheck
make integration
make lint
make test
docker compose exec -T app python -m coverage run -p --source=/app/src -m pytest -o addopts= -p no:cacheprovider /app/tests
docker compose exec -T app python -m coverage combine --keep
docker compose exec -T app python -m coverage report -m
docker compose exec -T app python -m coverage html -d /tmp/coverage-html
docker compose cp app:/tmp/coverage-html/. htmlcov/
docker compose stop -t 20 spark-master spark-worker
docker compose stop -t 20
git diff --check
```

The integration test executes metadata-quorum inspection, Python Kafka/MinIO probes, spark-submit and the temporary PostgreSQL probe through Docker. Its expected successful result is one synthetic row with mean_moisture=42.0, verified schema and matching PostgreSQL value. That complete result was **not observed**.

Read-only diagnostics also used `docker compose ps -a`, selected service logs, formatted `docker inspect` OOM/health fields, `docker stats`, `free -m`, `/proc/pressure/io`, service version commands, and Git ignore/status checks.

## Tests and coverage

- Full real integration suite: **8 passed, 2 failed**, 646.83 seconds. Failures: infrastructure timeout/cleanup timeout and lifecycle readiness deadline.
- Subsequent host Python 3.14.6 unit suite: **9 passed, 1 skipped**; integration deliberately not enabled.
- Python 3.12.7 container unit suite: **9 passed, 1 skipped**.
- Ruff lint and formatting: passed after final harness edits.
- Compose configuration and Git whitespace checks: passed.
- Combined completed Python container probe/unit coverage: **79% (188 statements, 39 missed)**.
- Coverage does not include Spark/JVM code. The healthcheck module has no instrumented coverage in this report; its earlier real readiness invocation succeeded.
- Export: ignored `htmlcov/index.html`. Coverage files and HTML, local logs, staged data and .env remain ignored.

## Final state and next action

All six YieldLens services are stopped intentionally. App, MinIO and PostgreSQL exited 0; Kafka and both Spark daemons exited 143 following the requested stop signals. Initializers exited 0. All OOM flags were false.

The PostgreSQL and MinIO temporary records are cleaned up; no generated files were found in the dedicated Spark smoke volume. Existing volumes remain available for the next run.

The next action is an approved rerun of Phase 1.5 in a quieter host window or on a host with adequate available resources, using the repaired Spark handoff. Do not begin Phase 2 until the actual Parquet round trip and full aggregate path pass. The current configuration remains a single-host development profile, not a production-readiness claim.
