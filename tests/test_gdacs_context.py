from src.live_data import DataEnvelope
from src import gdacs_context


def test_gdacs_context_normalizes_geojson(monkeypatch):
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [91.7, 26.1]},
                "properties": {
                    "eventtype": "FL",
                    "eventid": 123,
                    "name": "Example Flood",
                    "country": "India",
                    "alertlevel": "orange",
                    "severity": "moderate",
                    "fromdate": "2026-08-30",
                    "todate": "2026-08-31",
                },
            }
        ],
    }

    def fake_fetch(**kwargs):
        return DataEnvelope(
            source="Global Disaster Alert and Coordination System (GDACS)",
            mode="LIVE",
            fetched_at="2026-08-31T03:30:00+00:00",
            payload=payload,
            source_url=kwargs["url"],
        )

    monkeypatch.setattr(gdacs_context, "fetch_json_with_cache", fake_fetch)
    result = gdacs_context.fetch_gdacs_events(days=7)
    assert result["mode"] == "LIVE"
    assert len(result["events"]) == 1
    event = result["events"][0]
    assert event["event_type"] == "FL"
    assert event["country"] == "India"
    assert event["latitude"] == 26.1
    assert event["longitude"] == 91.7
