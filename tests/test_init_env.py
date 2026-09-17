"""Exercise private first-run configuration without starting services."""

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def initialize(directory):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/init_env.py")],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=10,
    )


@pytest.mark.skipif(os.name != "posix", reason="Linux/WSL file permissions")
def test_initializer_creates_private_unique_secrets_and_preserves_existing(tmp_path):
    (tmp_path / ".env.example").write_text((ROOT / ".env.example").read_text())
    first = initialize(tmp_path)
    assert first.returncode == 0
    path = tmp_path / ".env"
    original = path.read_bytes()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    values = dict(
        line.split("=", 1)
        for line in original.decode().splitlines()
        if line and not line.startswith("#")
    )
    secrets = [values[key] for key in ("MINIO_ROOT_PASSWORD", "POSTGRES_PASSWORD")]
    assert all(len(value) >= 32 and not value.startswith("change-me") for value in secrets)
    assert len(set(secrets)) == 2
    assert all(value not in first.stdout + first.stderr for value in secrets)
    second = initialize(tmp_path)
    assert second.returncode != 0
    assert path.read_bytes() == original
    assert all(value not in second.stdout + second.stderr for value in secrets)
