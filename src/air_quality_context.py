"""Open-Meteo air-quality context for arbitrary coordinates.

This is situational evidence only. It does not alter the deterministic SIH26191
risk equation without an explicit calibrated mapping.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlencode

from src.live_data import fetch_json_with_cache


AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"


def fetch_air_quality_at_location(name: str, latitude: float, longitude: float, *, timeout: float = 7.0) -> dict:
    params = urlencode(
        {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "current": "us_aqi,pm2_5,pm10,nitrogen_dioxide,ozone,dust,uv_index",
            "hourly": "us_aqi,pm2_5,pm10,dust",
            "forecast_days": 2,
            "timezone": "auto",
        }
    )
    key = hashlib.sha1(f"{latitude:.4f},{longitude:.4f}".encode("utf-8")).hexdigest()[:14]
    envelope = fetch_json_with_cache(
        source="Open-Meteo Air Quality API",
        url=f"{AIR_QUALITY_URL}?{params}",
        cache_path=Path("data/cache/open_meteo_air") / f"air_{key}.json",
        timeout=timeout,
    )
    payload = envelope.payload or {}
    return {
        "source": envelope.source,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": envelope.source_url,
        "location": name,
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "timezone": payload.get("timezone"),
        "current": payload.get("current", {}) if isinstance(payload, dict) else {},
        "current_units": payload.get("current_units", {}) if isinstance(payload, dict) else {},
        "hourly": payload.get("hourly", {}) if isinstance(payload, dict) else {},
        "hourly_units": payload.get("hourly_units", {}) if isinstance(payload, dict) else {},
    }
