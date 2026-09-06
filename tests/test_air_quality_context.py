from src.live_data import DataEnvelope
from src import air_quality_context


def test_air_quality_context_normalizes_live_payload(monkeypatch):
    payload = {
        "latitude": 19.8,
        "longitude": 85.8,
        "timezone": "Asia/Kolkata",
        "current": {"us_aqi": 58, "pm2_5": 21.4, "pm10": 39.0, "ozone": 72.0},
        "current_units": {"us_aqi": "", "pm2_5": "μg/m³", "pm10": "μg/m³", "ozone": "μg/m³"},
        "hourly": {"time": ["2026-09-06T12:00"], "us_aqi": [58]},
        "hourly_units": {"us_aqi": ""},
    }
    captured = {}

    def fake_fetch(**kwargs):
        captured.update(kwargs)
        return DataEnvelope(
            source="Open-Meteo Air Quality API",
            mode="LIVE",
            fetched_at="2026-09-06T06:30:00+00:00",
            payload=payload,
            source_url=kwargs["url"],
        )

    monkeypatch.setattr(air_quality_context, "fetch_json_with_cache", fake_fetch)
    result = air_quality_context.fetch_air_quality_at_location("Puri", 19.8, 85.8)

    assert result["mode"] == "LIVE"
    assert result["location"] == "Puri"
    assert result["current"]["us_aqi"] == 58
    assert result["current"]["pm2_5"] == 21.4
    assert result["timezone"] == "Asia/Kolkata"
    assert "latitude=19.8" in captured["url"]
    assert "longitude=85.8" in captured["url"]
    assert "us_aqi%2Cpm2_5%2Cpm10" in captured["url"]


def test_air_quality_context_handles_empty_cached_payload(monkeypatch):
    def fake_fetch(**kwargs):
        return DataEnvelope(
            source="Open-Meteo Air Quality API",
            mode="CACHED",
            fetched_at="2026-09-06T06:00:00+00:00",
            payload=None,
            source_url=kwargs["url"],
            stale=True,
        )

    monkeypatch.setattr(air_quality_context, "fetch_json_with_cache", fake_fetch)
    result = air_quality_context.fetch_air_quality_at_location("Puri", 19.8, 85.8)

    assert result["mode"] == "CACHED"
    assert result["stale"] is True
    assert result["current"] == {}
    assert result["hourly"] == {}
