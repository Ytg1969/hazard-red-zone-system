from src import earthquake_context
from src.live_data import DataEnvelope


def test_usgs_context_parses_events_without_network(monkeypatch):
    payload = {
        "features": [
            {
                "properties": {"mag": 4.2, "place": "Test event", "time": 1234567890, "url": "https://example.test/event"},
                "geometry": {"coordinates": [91.7, 26.2, 12.0]},
            }
        ]
    }

    def fake_fetch(**kwargs):
        assert "earthquake.usgs.gov/fdsnws/event/1/query" in kwargs["url"]
        return DataEnvelope(
            source="USGS FDSN Earthquake Catalog",
            mode="LIVE",
            fetched_at="2026-08-31T00:00:00+00:00",
            payload=payload,
            stale=False,
            source_url=kwargs["url"],
        )

    monkeypatch.setattr(earthquake_context, "fetch_json_with_cache", fake_fetch)
    result = earthquake_context.fetch_recent_earthquakes("Guwahati")
    assert result["mode"] == "LIVE"
    assert result["events"][0]["magnitude"] == 4.2
    assert result["events"][0]["latitude"] == 26.2
    assert result["events"][0]["depth_km"] == 12.0


def test_usgs_context_rejects_unknown_city():
    try:
        earthquake_context.fetch_recent_earthquakes("Unknown City")
    except ValueError as exc:
        assert "requires one of" in str(exc)
    else:
        raise AssertionError("unknown city must be rejected before network access")
