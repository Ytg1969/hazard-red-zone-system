"""Optional USGS earthquake context adapter with LIVE→CACHED behavior."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from src.live_data import fetch_json_with_cache

CITY_CENTERS = {
    "Puri": (19.8135, 85.8312),
    "Guwahati": (26.1445, 91.7362),
    "Chennai": (13.0827, 80.2707),
}

USGS_QUERY = "https://earthquake.usgs.gov/fdsnws/event/1/query"


def fetch_recent_earthquakes(city: str, *, days: int = 30, radius_km: int = 500, min_magnitude: float = 2.5) -> dict:
    """Fetch recent earthquakes near a demo city from the official USGS FDSN API.

    This is contextual evidence only; it does not directly alter the deterministic
    risk score. Successful responses are LIVE and cached responses are CACHED.
    """
    if city not in CITY_CENTERS:
        raise ValueError(f"earthquake context requires one of {sorted(CITY_CENTERS)}")
    lat, lon = CITY_CENTERS[city]
    start = (datetime.now(timezone.utc) - timedelta(days=max(1, int(days)))).strftime("%Y-%m-%dT%H:%M:%S")
    params = urlencode({
        "format": "geojson",
        "latitude": lat,
        "longitude": lon,
        "maxradiuskm": int(radius_km),
        "starttime": start,
        "minmagnitude": float(min_magnitude),
        "orderby": "time",
        "limit": 100,
    })
    envelope = fetch_json_with_cache(
        source="USGS FDSN Earthquake Catalog",
        url=f"{USGS_QUERY}?{params}",
        cache_path=Path("data/cache") / f"usgs_{city.lower()}_earthquakes.json",
        timeout=8.0,
    )
    events = []
    for feature in (envelope.payload or {}).get("features", []):
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [None, None, None])
        events.append({
            "magnitude": props.get("mag"),
            "place": props.get("place"),
            "time": props.get("time"),
            "detail_url": props.get("url"),
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "depth_km": coords[2] if len(coords) > 2 else None,
        })
    return {
        "source": envelope.source,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": envelope.source_url,
        "events": events,
    }
