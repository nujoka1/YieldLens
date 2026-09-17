# Phase 1 and Phase 1.5 status

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

Phase 1 scaffolding exists. **Phase 1.5 is PARTIAL; Phase 2 is not approved or ready to begin.**

Validation date: 2026-09-05. Repository: `yieldlens-nigeria`.

| Component | Verified version | Result |
|---|---|---|
| Kafka | 3.9.1, KRaft broker/controller | Ready; metadata quorum and message round trip passed |
| MinIO | RELEASE.2025-04-22T22-12-26Z; Go 1.24.2 | API/console, zones and object checksum passed |
| MinIO client initializer | RELEASE.2025-04-16T18-13-26Z image | Exited 0; required prefixes verified |
| Spark master/worker | 3.5.6 | Worker registration passed; Parquet job not verified |
| PostgreSQL | 17.6, Alpine | Authenticated connectivity, schemas and temporary-table transaction passed |
| Python development image | 3.12.7 | 9 unit tests passed; full-stack test skipped in final unit run |
| Docker Compose | v5.4.0 | Configuration validated |

All six long-running services reached healthy state together. The full integration run then failed: Spark submission exceeded 240 seconds; its cleanup also timed out. A stdin-handoff defect in the smoke harness was found and corrected, but the corrected full test was not rerun under the observed sustained host I/O pressure.

The initial full suite reported **8 passed, 2 failed**. After stopping Spark, the host and container unit suites each reported **9 passed, 1 explicitly skipped**. Combined Python 3.12 unit/completed-probe coverage was **79%**. This does not establish Spark or end-to-end success.

Final state: every YieldLens service deliberately stopped; named volumes preserved; no observed container OOM kills. The exact synthetic MinIO object was removed and its absence verified. The dedicated Spark smoke volume contained no files. Synthetic Kafka records remain under normal retention.

No real agricultural data, full simulator, machine learning, risk engine, scalability experiment, dashboard or production deployment was implemented.

See [runtime verification](runtime-verification.md) for exact checks, failures, resource evidence and commands.
