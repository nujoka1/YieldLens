"""Reject non-synthetic or incorrect aggregates before any database connection."""

import pytest

from yieldlens.smoke import postgres_probe


@pytest.mark.parametrize(
    "record",
    [
        {},
        {"synthetic": False, "mean_moisture": 42.0},
        {"synthetic": True, "mean_moisture": 0.0},
    ],
)
def test_invalid_smoke_aggregate_is_rejected(record):
    with pytest.raises(ValueError, match="Unexpected synthetic aggregate"):
        postgres_probe(record)
