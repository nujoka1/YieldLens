import json

import structlog

from yieldlens.logging import configure_logging


def test_structured_log_is_json(capsys) -> None:
    configure_logging("INFO")
    structlog.get_logger("test").info("sample_event", record_count=200)

    record = json.loads(capsys.readouterr().out)
    assert record["event"] == "sample_event"
    assert record["record_count"] == 200
    assert record["level"] == "info"
    assert "timestamp" in record
