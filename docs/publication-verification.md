# Source publication checks — 18 September 2026

This publication adds the Phase 1 implementation and Windows WSL2 guide. It does not complete Phase 1.5 or certify Windows support.

## Checks performed without starting Docker services

- Original checkout: `make check` passed quiet Compose validation and Ruff lint/format. Pytest: **9 passed, 1 failed, 1 skipped in 53.62 seconds**; host coverage **46%**. The new credential-initializer subprocess exceeded its unchanged 10-second deadline.
- Clean publication checkout: quiet Compose validation using the existing private environment file passed; its contents were not printed or copied.
- Clean publication checkout: Ruff lint/format and Git whitespace checks passed.
- Unchanged full unit-suite retry from publication checkout: **8 passed, 2 failed, 1 skipped in 72.40 seconds**; coverage **34% (188 statements, 125 missed)**. Failures: initializer subprocess timeout (10 seconds) and lifecycle readiness deadline (15 seconds).
- Both runs used the existing **Python 3.14.6** host environment, not the supported Python 3.12 Windows/WSL environment. No Python 3.12 runtime test was available for this publication.
- Integration was explicitly skipped. No images were pulled/built and no Docker services were started during this publication task.

The subprocess deadline failures are observed facts; their cause was not isolated here. Prior host freezes and storage errors mean another stack run on this PC is not appropriate. Timeouts were not relaxed, failures were not mocked, and a passing unit suite is not claimed.

## Publication boundary

The source was selected by an explicit allowlist and copied into a clean checkout based on the existing GitHub main branch. Existing GitHub license/history were preserved; unrelated local history and its tracked office template were not imported.

Selected text was checked for exact local credential matches and common private-key/GitHub-token patterns. This is a scoped secret check, not a comprehensive security audit. No .env, office documents, archives, datasets, virtual environments, runtime logs, generated coverage or Docker-volume contents are included. Empty data/log directory markers are intentional.

New guidance uses Linux commands within Ubuntu WSL2 and Docker Desktop Linux containers; native Windows Python/Make is not claimed to work. LF rules preserve Linux-oriented source/configuration line endings. The app test mounts include the setup script and public template, never the private environment file.

## Outstanding verification

Run the documented lightweight checks with Python 3.12 on a healthy target machine first. Investigate failures before starting services. Full-stack readiness, Spark Parquet, the end-to-end aggregate and Windows execution remain unverified. Phase 2 still requires approval after Phase 1.5 succeeds.
