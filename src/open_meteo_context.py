"""Reliable no-auth weather context for the three-city demo.

Open-Meteo provides forecast/current weather data without an API key. This
adapter is contextual evidence only: it never silently modifies the frozen
hazard/risk score. LIVE responses are cached; failures fall back to CACHED.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from src.live_data import fetch_json_with_cache

CITY_CENTERS = {
    "Puri": (19.8135, 85.8312),
    "Guwahati": (26.1445, 91.7362),
    "Chennai": (13.0827, 80.2707),
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_weather_context(city: str, *, timeout: float = 6.0) -> dict:
    if city not in CITY_CENTERS:
        raise ValueError(f"weather context requires one of {sorted(CITY_CENTERS)}")

    lat, lon = CITY_CENTERS[city]
    params = urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,rain,weather_code,wind_speed_10m,wind_gusts_10m",
            "hourly": "precipitation_probability,precipitation,rain,wind_speed_10m,wind_gusts_10m",
            "forecast_days": 2,
            "timezone": "auto",
        }
    )
    envelope = fetch_json_with_cache(
        source="Open-Meteo Forecast API",
        url=f"{OPEN_METEO_URL}?{params}",
        cache_path=Path("data/cache/open_meteo") / f"{city.lower()}_weather.json",
        timeout=timeout,
    )

    payload = envelope.payload or {}
    current = payload.get("current", {}) if isinstance(payload, dict) else {}
    hourly = payload.get("hourly", {}) if isinstance(payload, dict) else {}
    units = payload.get("current_units", {}) if isinstance(payload, dict) else {}

    return {
        "source": envelope.source,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": envelope.source_url,
        "city": city,
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "timezone": payload.get("timezone"),
        "current": current,
        "current_units": units,
        "hourly": hourly,
    }
