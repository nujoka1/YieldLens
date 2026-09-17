# Windows setup (WSL2 + Docker Desktop)

Status: instructions prepared on 18 September 2026; **not runtime-tested on Windows**. Phase 1.5 remains incomplete. This guide does not claim the full stack is reliable or production-ready.

## Before installing

Use a healthy Windows machine with hardware virtualization and a supported Windows version. Check the current [Docker Desktop Windows requirements](https://docs.docker.com/desktop/setup/install/windows-install/) before installation, including license terms.

The previous 8 GB Linux host froze under load, had no swap, and showed heavy disk pressure. Separate later diagnostics found read errors on an attached drive; the exact cause of earlier freezes is unresolved. Moving to Windows alone does not resolve those issues. Do not use a suspect disk for this checkout or Docker storage. Prefer a machine with more memory headroom and healthy local storage; no minimum for this full stack has been validated.

The configured long-running container ceilings total about 3.25 GiB, excluding initializers, image builds, Windows, WSL and other applications. Ceilings are not a complete host budget, nor a guarantee that Kafka's 512 MiB ceiling is sufficient. Do not raise limits, change swap, or modify WSL resource configuration just to force a pass.

## 1. Install WSL (Administrator PowerShell)

These are manual installation steps on the target Windows machine, not commands run by the publication task.

```powershell
wsl --install -d Ubuntu-24.04
# Restart Windows if requested, then complete Ubuntu's username/password setup.
wsl --update
wsl --list --verbose
```

Ubuntu-24.04 should show VERSION 2. If an existing installation shows VERSION 1, review [Microsoft's WSL instructions](https://learn.microsoft.com/en-us/windows/wsl/install) before converting it. Do not reinstall an existing distribution or delete its data.

Install and open Docker Desktop. Use the WSL2 backend and **Linux containers**, and enable Ubuntu-24.04 under Settings > Resources > WSL Integration. Follow [Docker's WSL guide](https://docs.docker.com/desktop/features/wsl/). Do not install a second Docker Engine inside Ubuntu for this workflow.

From PowerShell, enter Ubuntu:

```powershell
wsl -d Ubuntu-24.04
```

**All subsequent command blocks run in Ubuntu Bash, not PowerShell or Command Prompt.** Native Windows Python is not the test environment: the lifecycle test uses POSIX signals and pipe selection.

## 2. Clone inside the Linux filesystem

```bash
sudo apt update
sudo apt install -y git make python3.12 python3.12-venv curl
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/nujoka1/YieldLens.git
cd YieldLens
```

For an existing clone, inspect `git status` and preserve local changes before updating; do not clone over it. Keep the checkout under `~/projects`, not `/mnt/c`, OneDrive or the suspect external drive. Do not copy the old host's virtual environment, credentials or Docker volumes.

```bash
python3.12 --version
docker version
docker compose version
```

Docker should report both client and server. If not, start Docker Desktop and check WSL Integration. These checks do not start YieldLens services.

## 3. Private configuration and checks without containers

```bash
make setup PYTHON=python3.12
stat -c '%a %n' .env
git check-ignore .env
make validate
make lint
make test
```

Setup creates a Linux virtual environment, installs pinned dependencies and generates unique local credentials. Expected environment-file mode: 600; ignore check: `.env`. Never print or upload its contents. The initializer refuses to overwrite an existing file. Do not replace an existing `.env` when persistent volumes already contain credentials.

`make validate` quietly parses configuration; `make lint` checks source/formatting; `make test` exercises unit behavior and explicitly skips the opt-in infrastructure test. HTML coverage is generated locally in ignored `htmlcov/index.html`. Passing these checks does not validate Kafka or Spark. Python 3.12 is the intended runtime; the latest historical host results used Python 3.14 and are documented separately.

Review .env privately for port choices, but retain internal service hostnames. Published ports are localhost-only: Kafka 29092, MinIO 9000/19001, Spark 7077/8080/8081, PostgreSQL 5432.

## 4. Optional controlled infrastructure attempt

**Do not run this section on the freezing PC.** First save other work and confirm the target Windows machine and its storage are healthy. Historical Kafka instability is still unresolved.

In a second Ubuntu terminal, observe memory/I/O without changing limits:

```bash
free -m
cat /proc/pressure/memory /proc/pressure/io
docker stats
```

Use Windows Task Manager to observe host memory and disk activity too. Ctrl+C exits Docker stats without stopping services.

From the project terminal:

```bash
make pull
make up
```

These download images, build the app and start services sequentially with readiness waits. The current startup sequence can revisit dependencies and restart an exited container; a successful start message alone is not evidence of continuous stability. Do not repeatedly retry a failing startup.

If startup fails, the desktop becomes sluggish or a service exits unexpectedly, interrupt `make up` with Ctrl+C, then stop only this project:

```bash
docker compose stop -t 20
docker compose ps -a
```

Preserve evidence; do not delete volumes, terminate unrelated processes or raise limits.

## 5. Readiness and the synthetic integration test

Only after successful, stable startup:

```bash
docker compose ps -a
docker compose exec -T app python -m yieldlens.healthcheck
curl --fail http://127.0.0.1:9000/minio/health/ready
curl --fail http://127.0.0.1:8080/json/
```

Expected: Kafka, MinIO, Spark master/worker, PostgreSQL and app all healthy; initializers exited 0; Spark JSON includes an ALIVE worker; application readiness exits 0.

Then, and only then:

```bash
make integration
# After successful integration, combine app-side instrumented coverage:
make coverage
```

Expected successful integration: a synthetic record round trip, matching MinIO checksum, one Parquet row with verified schema and mean_moisture 42.0, followed by a verified temporary PostgreSQL aggregate. These expected outputs have **not** been achieved end to end on the original host or verified on Windows. Record actual failures without replacing them with mocks.

Temporary MinIO/Parquet files are targeted for cleanup; the SQL table is temporary. Synthetic Kafka messages remain under normal retention. Do not invoke the low-level prepare command manually: it prints a temporary signed object URL intended for the test harness.

## 6. Browser endpoints and shutdown

On the Windows browser, try MinIO at http://localhost:19001 and Spark at http://localhost:8080 (worker: http://localhost:8081). There is **no dashboard yet**. Use your private .env credentials for MinIO, never the example placeholders.

```bash
docker compose stop -t 20
docker compose ps -a
# Optional: remove project containers/network, retaining named volumes:
make down
```

Never use `down -v`, volume pruning, or a Docker Desktop factory reset as troubleshooting: these can destroy stored data. Stopping this Compose project does not require shutting down all WSL distributions.

## Troubleshooting

- Docker unavailable: confirm Docker Desktop is running, Linux containers are selected, and Ubuntu WSL Integration is enabled.
- Windows port conflict: inspect Task Manager or PowerShell `Get-NetTCPConnection -State Listen`; do not kill the owner. MinIO console has a configurable local port. The smoke test assumes Spark UI 8080 and MinIO API 9000.
- Permission errors: keep the clone in Ubuntu's Linux filesystem; do not solve them with chmod 777. Regenerate neither credentials nor database volumes.
- Authentication failure with existing PostgreSQL data: .env changes do not rotate the persisted database role. Reconcile credentials deliberately; do not delete the volume.
- Unhealthy container: inspect `docker compose logs --tail=50 SERVICE` locally. Before sharing logs, redact credentials and signed URLs. Never share full rendered Compose configuration or unrestricted docker inspect output.
- Suspected OOM: `docker inspect yieldlens-kafka-1 --format '{{.State.OOMKilled}} {{.State.ExitCode}}'` (default project name). Exit 137 alone is not proof of OOM, and a restart can obscure prior state.
- Freezing or disk errors: stop validation and investigate the host. Do not stress-test or repair suspect storage as part of this setup.

See [runtime verification](runtime-verification.md) for prior results and [Phase 1 status](phase-1.md). Dataset ingestion, full simulation, ML, risk scoring and dashboard remain deferred.
