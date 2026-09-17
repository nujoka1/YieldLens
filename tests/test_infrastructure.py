"""Opt-in real Docker checks."""

import json
import os
import subprocess
from urllib.request import urlopen

import pytest


def compose(*args, stdin=None, timeout=240):
    result = subprocess.run(
        ["docker", "compose", *args], input=stdin, text=True, capture_output=True, timeout=timeout
    )
    if result.returncode:
        # Never expose prepare output (it includes a short-lived signed URL).
        detail = result.stderr[-3000:] if "prepare" not in args else "prepare failed"
        raise RuntimeError(f"Compose operation {args[:3]} failed: {detail}")
    return result.stdout


@pytest.mark.integration
@pytest.mark.skipif(os.getenv("YIELDLENS_INTEGRATION") != "1", reason="Opt-in Docker test")
def test_real_infrastructure():
    states = [json.loads(line) for line in compose("ps", "--format", "json").splitlines()]
    running = {state["Service"]: state for state in states}
    for name in ("kafka", "minio", "postgres", "spark-master", "spark-worker", "app"):
        assert running[name]["Health"] == "healthy", f"{name} is not ready"
    for url in (
        "http://127.0.0.1:9000/minio/health/ready",
        "http://" + compose("port", "minio", "9001").strip(),
    ):
        with urlopen(url, timeout=10) as response:
            assert response.status == 200
    with urlopen("http://127.0.0.1:8080/json/", timeout=10) as response:
        master = json.load(response)
    assert any(worker["state"] == "ALIVE" for worker in master["workers"])
    quorum = compose(
        "exec",
        "-T",
        "-e",
        "KAFKA_HEAP_OPTS=-Xms32m -Xmx64m",
        "kafka",
        "/opt/kafka/bin/kafka-metadata-quorum.sh",
        "--bootstrap-server",
        "kafka:9092",
        "describe",
        "--status",
    )
    assert "LeaderId:" in quorum
    prepared = json.loads(
        compose(
            "exec",
            "-T",
            "app",
            "python",
            "-m",
            "coverage",
            "run",
            "-p",
            "--source=/app/src",
            "-m",
            "yieldlens.smoke",
            "prepare",
        )
    )
    try:
        assert all(
            topic["partitions"] == 6 and topic["replication_factor"] == 1
            for topic in prepared["topics"]
        )
        request_path = f"/tmp/yieldlens-smoke/{prepared['run_id']}.request.json"
        compose(
            "exec",
            "-T",
            "spark-master",
            "python3",
            "-c",
            "import os,sys; fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); "
            "f=os.fdopen(fd,'w'); f.write(sys.stdin.read()); f.close()",
            request_path,
            stdin=json.dumps(prepared),
        )
        output = compose(
            "exec",
            "-T",
            "spark-master",
            "timeout",
            "--kill-after=10s",
            "180s",
            "/opt/spark/bin/spark-submit",
            "--master",
            "spark://spark-master:7077",
            "--driver-memory",
            "512m",
            "--executor-memory",
            "512m",
            "--total-executor-cores",
            "1",
            "--conf",
            "spark.driver.host=spark-master",
            "--conf",
            "spark.sql.shuffle.partitions=2",
            "/opt/yieldlens/scripts/spark_smoke.py",
            request_path,
        )
        result = json.loads(
            next(
                line.split("=", 1)[1]
                for line in output.splitlines()
                if line.startswith("YIELDLENS_RESULT=")
            )
        )
        assert result["rows"] == 1
        assert result["mean_moisture"] == 42.0
        postgres = json.loads(
            compose(
                "exec",
                "-T",
                "app",
                "python",
                "-m",
                "coverage",
                "run",
                "-p",
                "--source=/app/src",
                "-m",
                "yieldlens.smoke",
                "postgres",
                stdin=json.dumps(result),
            )
        )
        assert postgres["postgres"] == "passed"
        print(json.dumps({"topics": prepared["topics"], "spark": result, "postgres": postgres}))
    finally:
        try:
            # Only the request file associated with this generated UUID is eligible for removal.
            compose(
                "exec",
                "-T",
                "spark-master",
                "python3",
                "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).unlink(missing_ok=True)",
                f"/tmp/yieldlens-smoke/{prepared['run_id']}.request.json",
            )
        finally:
            compose(
                "exec",
                "-T",
                "app",
                "python",
                "-m",
                "coverage",
                "run",
                "-p",
                "--source=/app/src",
                "-m",
                "yieldlens.smoke",
                "cleanup",
                stdin=json.dumps({"run_id": prepared["run_id"]}),
            )
