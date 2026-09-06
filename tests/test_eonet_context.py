from src.live_data import DataEnvelope
from src import eonet_context


def test_eonet_context_normalizes_latest_point_geometry(monkeypatch):
    payload = {
        "events": [
            {
                "id": "EONET_1",
                "title": "Example Flood",
                "categories": [{"id": "floods", "title": "Floods"}],
                "closed": None,
                "magnitudeValue": 3.2,
                "magnitudeUnit": "severity",
                "link": "https://eonet.gsfc.nasa.gov/api/v3/events/EONET_1",
                "geometry": [
                    {"date": "2026-09-05T00:00:00Z", "type": "Point", "coordinates": [85.7, 19.7]},
                    {"date": "2026-09-06T00:00:00Z", "type": "Point", "coordinates": [85.9, 19.9]},
                ],
            }
        ]
    }
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return DataEnvelope(
            source="NASA Earth Observatory Natural Event Tracker (EONET)",
            mode="LIVE",
            fetched_at="2026-09-06T06:30:00+00:00",
            payload=payload,
            source_url=kwargs["url"],
        )

    monkeypatch.setattr(eonet_context, "fetch_json_with_cache", fake_fetch)
    result = eonet_context.fetch_eonet_events(category="floods", days=14, limit=500, bbox=(80.0, 25.0, 90.0, 15.0))

    assert result["mode"] == "LIVE"
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["event_id"] == "EONET_1"
    assert event["categories"] == "Floods"
    assert event["latest_date"] == "2026-09-06T00:00:00Z"
    assert event["latitude"] == 19.9
    assert event["longitude"] == 85.9
    assert "category=floods" in captured["url"]
    assert "days=14" in captured["url"]
    assert "limit=200" in captured["url"]
    assert "bbox=80.0%2C25.0%2C90.0%2C15.0" in captured["url"]


def test_eonet_context_skips_invalid_rows_and_handles_nonpoint_geometry(monkeypatch):
    payload = {
        "events": [
            "invalid",
            {
                "id": "EONET_POLY",
                "title": "Polygon Event",
                "categories": [],
                "geometry": [{"date": "2026-09-06", "coordinates": [[85.0, 19.0], [86.0, 20.0]]}],
            },
        ]
    }

    def fake_fetch(**kwargs):
        return DataEnvelope(
            source="NASA Earth Observatory Natural Event Tracker (EONET)",
            mode="CACHED",
            fetched_at="2026-09-06T06:00:00+00:00",
            payload=payload,
            source_url=kwargs["url"],
            stale=True,
        )

    monkeypatch.setattr(eonet_context, "fetch_json_with_cache", fake_fetch)
    result = eonet_context.fetch_eonet_events(days=0, limit=0)

    assert result["mode"] == "CACHED"
    assert result["stale"] is True
    assert len(result["events"]) == 1
    assert result["events"][0]["event_id"] == "EONET_POLY"
    assert result["events"][0]["latitude"] is None
    assert result["events"][0]["longitude"] is None
