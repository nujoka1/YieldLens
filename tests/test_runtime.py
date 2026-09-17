"""Verify the actual lifecycle process starts and shuts down on SIGTERM."""

import json
import select
import signal
import subprocess
import sys


def test_runtime_graceful_shutdown():
    process = subprocess.Popen(
        [sys.executable, "-m", "coverage", "run", "-p", "--source=src", "-m", "yieldlens.runtime"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert select.select([process.stdout], [], [], 15)[0], "Runtime did not become ready"
        ready = json.loads(process.stdout.readline())
        assert ready["event"] == "application_ready"
        process.send_signal(signal.SIGTERM)
        output, errors = process.communicate(timeout=15)
        assert process.returncode == 0, errors
        events = [json.loads(line)["event"] for line in output.splitlines()]
        assert events == ["shutdown_requested", "application_stopped"]
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
