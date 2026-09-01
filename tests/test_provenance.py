from datetime import datetime, timezone

from src.provenance import (
    default_provenance_register,
    freshness_status,
    normalize_mode,
    provenance_record,
    source_health,
)


def test_normalize_mode_rejects_unknown_values():
    assert normalize_mode("live") == "LIVE"
    assert normalize_mode("cached") == "CACHED"
    assert normalize_mode("something-else") == "DEMO"


def test_freshness_status_boundaries():
    now = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    assert freshness_status("2026-09-01T11:50:00Z", now=now)["status"] == "FRESH"
    assert freshness_status("2026-09-01T11:00:00Z", now=now)["status"] == "AGING"
    assert freshness_status("2026-09-01T08:00:00Z", now=now)["status"] == "STALE"
    assert freshness_status(None, now=now)["status"] == "UNKNOWN"


def test_source_health_degraded_on_error():
    health = source_health({"source": "X", "mode": "LIVE", "error": "timeout"})
    assert health["operational_state"] == "DEGRADED"
    assert health["mode"] == "LIVE"


def test_demo_source_is_never_presented_as_healthy_live():
    health = source_health({"source": "Demo", "mode": "DEMO", "fetched_at": "2026-09-01T12:00:00Z"})
    assert health["operational_state"] == "DEMO_ONLY"


def test_provenance_register_keeps_external_context_out_of_risk():
    rows = default_provenance_register()
    external = [row for row in rows if row["source"] in {"Open-Meteo", "USGS FDSN", "GDACS", "NASA EONET", "NRSC/ISRO Bhuvan WMS"}]
    assert external
    assert all(row["affects_risk"] is False for row in external)


def test_provenance_record_normalizes_mode():
    row = provenance_record(dataset="x", source="y", mode="cached", role="context", affects_risk=False)
    assert row["mode"] == "CACHED"
