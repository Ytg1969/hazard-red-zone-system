"""Location lookup for arbitrary-city situational context.

Uses Open-Meteo's no-auth geocoding API while connected. Results are contextual
metadata only and never modify the deterministic risk score. Explicit offline
mode never attempts geocoding network access.
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlencode

from src.live_data import fetch_json_with_cache
from src.runtime_mode import offline_mode

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

OFFLINE_REFERENCE_LOCATIONS = [
    {"name": "Puri", "label": "Puri, Odisha, India", "latitude": 19.8135, "longitude": 85.8312, "country": "India", "country_code": "IN", "admin1": "Odisha", "timezone": "Asia/Kolkata", "population": None},
    {"name": "Guwahati", "label": "Guwahati, Assam, India", "latitude": 26.1445, "longitude": 91.7362, "country": "India", "country_code": "IN", "admin1": "Assam", "timezone": "Asia/Kolkata", "population": None},
    {"name": "Chennai", "label": "Chennai, Tamil Nadu, India", "latitude": 13.0827, "longitude": 80.2707, "country": "India", "country_code": "IN", "admin1": "Tamil Nadu", "timezone": "Asia/Kolkata", "population": None},
]


def _cache_key(query: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_")
    return cleaned[:80] or "location"


def search_locations(query: str, *, count: int = 8, timeout: float = 6.0) -> dict:
    query = str(query or "").strip()
    if len(query) < 2:
        return {"source": "Open-Meteo Geocoding API", "mode": "DEMO", "stale": False, "results": [], "error": "Enter at least two characters."}

    if offline_mode():
        term = query.casefold()
        matches = [row for row in OFFLINE_REFERENCE_LOCATIONS if term in row["label"].casefold() or term in row["name"].casefold()]
        return {
            "source": "Bundled offline location index",
            "mode": "DEMO",
            "stale": False,
            "access_status": "OFFLINE",
            "results": matches[: max(1, min(int(count), 20))],
        }

    params = urlencode({"name": query, "count": max(1, min(int(count), 20)), "language": "en", "format": "json"})
    envelope = fetch_json_with_cache(
        source="Open-Meteo Geocoding API",
        url=f"{GEOCODING_URL}?{params}",
        cache_path=Path("data/cache/geocoding") / f"{_cache_key(query)}.json",
        timeout=timeout,
    )
    payload = envelope.payload or {}
    rows = payload.get("results", []) if isinstance(payload, dict) else []
    results = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        lat = row.get("latitude")
        lon = row.get("longitude")
        if lat is None or lon is None:
            continue
        parts = [row.get("name"), row.get("admin1"), row.get("country")]
        label = ", ".join(str(x) for x in parts if x)
        results.append({
            "name": row.get("name") or query,
            "label": label or query,
            "latitude": float(lat),
            "longitude": float(lon),
            "country": row.get("country"),
            "country_code": row.get("country_code"),
            "admin1": row.get("admin1"),
            "timezone": row.get("timezone"),
            "population": row.get("population"),
        })
    return {
        "source": envelope.source,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": envelope.source_url,
        "results": results,
    }
