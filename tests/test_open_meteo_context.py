from src.live_data import DataEnvelope
from src import open_meteo_context


def test_weather_context_normalizes_live_payload(monkeypatch):
    payload = {
        "latitude": 19.8,
        "longitude": 85.8,
        "timezone": "Asia/Kolkata",
        "current": {"temperature_2m": 30.5, "precipitation": 1.2, "wind_speed_10m": 14.0},
        "current_units": {"temperature_2m": "°C", "precipitation": "mm", "wind_speed_10m": "km/h"},
        "hourly": {"time": ["2026-08-31T09:00"], "precipitation_probability": [70]},
    }

    def fake_fetch(**kwargs):
        return DataEnvelope(
            source="Open-Meteo Forecast API",
            mode="LIVE",
            fetched_at="2026-08-31T03:30:00+00:00",
            payload=payload,
            source_url=kwargs["url"],
        )

    monkeypatch.setattr(open_meteo_context, "fetch_json_with_cache", fake_fetch)
    result = open_meteo_context.fetch_weather_context("Puri")
    assert result["mode"] == "LIVE"
    assert result["current"]["temperature_2m"] == 30.5
    assert result["current"]["precipitation"] == 1.2
    assert result["timezone"] == "Asia/Kolkata"
