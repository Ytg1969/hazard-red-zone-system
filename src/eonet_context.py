"""NASA EONET natural-event context with LIVE→CACHED behavior.

EONET is global situational context only. It is never treated as a calibrated
local hazard score without an explicit source-specific mapping.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from src.live_data import fetch_json_with_cache

EONET_EVENTS_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

CATEGORY_MAP = {
    "All calamities": None,
    "Flood": "floods",
    "Cyclone / Severe Storm": "severeStorms",
    "Earthquake": "earthquakes",
    "Landslide": "landslides",
    "Wildfire": "wildfires",
    "Volcano": "volcanoes",
    "Drought": "drought",
    "Dust / Haze": "dustHaze",
    "Sea / Lake Ice": "seaLakeIce",
    "Snow": "snow",
    "Temperature Extremes": "tempExtremes",
}


def fetch_eonet_events(*, category: str | None = None, days: int = 30, limit: int = 100, bbox: tuple[float, float, float, float] | None = None, timeout: float = 8.0) -> dict:
    params: dict[str, object] = {
        "status": "all",
        "days": max(1, int(days)),
        "limit": max(1, min(int(limit), 200)),
    }
    if category:
        params["category"] = category
    if bbox is not None:
        min_lon, max_lat, max_lon, min_lat = bbox
        params["bbox"] = f"{min_lon},{max_lat},{max_lon},{min_lat}"

    query = urlencode(params)
    cache_bits = [category or "all", str(days)]
    if bbox is not None:
        cache_bits.append("local")
    envelope = fetch_json_with_cache(
        source="NASA Earth Observatory Natural Event Tracker (EONET)",
        url=f"{EONET_EVENTS_URL}?{query}",
        cache_path=Path("data/cache/eonet") / ("_".join(cache_bits) + ".json"),
        timeout=timeout,
    )

    payload = envelope.payload or {}
    normalized = []
    for event in payload.get("events", []) if isinstance(payload, dict) else []:
        if not isinstance(event, dict):
            continue
        geometry = event.get("geometry") or []
        latest = geometry[-1] if geometry else {}
        coords = latest.get("coordinates") if isinstance(latest, dict) else None
        lon = lat = None
        if isinstance(coords, list) and len(coords) >= 2 and not isinstance(coords[0], list):
            lon, lat = coords[0], coords[1]
        categories = event.get("categories") or []
        normalized.append({
            "event_id": event.get("id"),
            "title": event.get("title"),
            "categories": ", ".join(str(x.get("title")) for x in categories if isinstance(x, dict) and x.get("title")),
            "closed": event.get("closed"),
            "latest_date": latest.get("date") if isinstance(latest, dict) else None,
            "magnitude": event.get("magnitudeValue"),
            "magnitude_unit": event.get("magnitudeUnit"),
            "latitude": lat,
            "longitude": lon,
            "api_link": event.get("link"),
        })
    return {
        "source": envelope.source,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": envelope.source_url,
        "events": normalized,
    }
