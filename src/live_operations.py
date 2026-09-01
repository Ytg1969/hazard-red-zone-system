"""Real-time situational-source orchestration for the EOC operations portal.

This module intentionally keeps external LIVE/CACHED context separate from the
frozen deterministic risk model. It provides one resilient call surface for UI
pages and future API/service layers while preserving explicit source status.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Callable

from src.air_quality_context import fetch_air_quality_at_location
from src.earthquake_context import CITY_CENTERS, fetch_recent_earthquakes_at_location
from src.eonet_context import fetch_eonet_events
from src.gdacs_context import fetch_gdacs_events
from src.imd_context import fetch_imd_context
from src.live_alerts import fetch_disaster_alerts
from src.open_meteo_context import fetch_weather_at_location
from src.spatial_analysis import haversine_km


def _safe_call(label: str, fn: Callable[[], dict]) -> dict:
    """Execute a live adapter without allowing one source failure to break the hub."""
    try:
        result = fn()
        if not isinstance(result, dict):
            raise TypeError(f"{label} adapter returned a non-dict response")
        return result
    except Exception as exc:
        return {
            "source": label,
            "mode": "DEMO",
            "stale": False,
            "error": str(exc),
        }


def _distance_filter(events: list[dict], latitude: float, longitude: float, radius_km: float) -> list[dict]:
    nearby: list[dict] = []
    for row in events:
        try:
            event_lat = float(row.get("latitude"))
            event_lon = float(row.get("longitude"))
        except (TypeError, ValueError):
            continue
        distance = haversine_km(latitude, longitude, event_lat, event_lon)
        if distance <= radius_km:
            item = dict(row)
            item["distance_km"] = round(distance, 1)
            nearby.append(item)
    nearby.sort(key=lambda row: float(row.get("distance_km") or 10**9))
    return nearby


def _resolve_location(city: str, latitude: float | None, longitude: float | None) -> tuple[float, float]:
    if latitude is not None and longitude is not None:
        return float(latitude), float(longitude)
    if city in CITY_CENTERS:
        return CITY_CENTERS[city]
    raise ValueError("latitude and longitude are required for locations outside the bundled reference cities")


def fetch_operations_snapshot(
    city: str,
    *,
    latitude: float | None = None,
    longitude: float | None = None,
    days: int = 7,
    radius_km: int = 500,
    min_magnitude: float = 2.5,
) -> dict:
    """Fetch an EOC-friendly real-time/context snapshot.

    Calls to independent external sources are executed concurrently to avoid
    serial network latency. The result is situational context only: nothing
    returned by this function is automatically mapped into H/E/V/A or the
    baseline risk score.
    """
    latitude, longitude = _resolve_location(city, latitude, longitude)

    calls: dict[str, tuple[str, Callable[[], dict]]] = {
        "weather": (
            "Open-Meteo Forecast API",
            lambda: fetch_weather_at_location(city, latitude, longitude),
        ),
        "air_quality": (
            "Open-Meteo Air Quality API",
            lambda: fetch_air_quality_at_location(city, latitude, longitude),
        ),
        "usgs": (
            "USGS FDSN Earthquake Catalog",
            lambda: fetch_recent_earthquakes_at_location(
                city,
                latitude,
                longitude,
                days=days,
                radius_km=radius_km,
                min_magnitude=min_magnitude,
            ),
        ),
        "gdacs": (
            "Global Disaster Alert and Coordination System (GDACS)",
            lambda: fetch_gdacs_events(days=days),
        ),
        "eonet": (
            "NASA Earth Observatory Natural Event Tracker (EONET)",
            lambda: fetch_eonet_events(days=days, limit=100),
        ),
        "imd": (
            "India Meteorological Department (IMD)",
            lambda: fetch_imd_context(city),
        ),
        "sachet": ("NDMA SACHET", fetch_disaster_alerts),
    }

    sources: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=len(calls), thread_name_prefix="live-source") as executor:
        future_map = {
            executor.submit(_safe_call, label, fn): key
            for key, (label, fn) in calls.items()
        }
        for future in as_completed(future_map):
            key = future_map[future]
            sources[key] = future.result()

    weather = sources["weather"]
    air = sources["air_quality"]
    usgs = sources["usgs"]
    gdacs = sources["gdacs"]
    eonet = sources["eonet"]
    imd = sources["imd"]
    sachet = sources["sachet"]

    gdacs_nearby = _distance_filter(list(gdacs.get("events", [])), latitude, longitude, radius_km)
    eonet_nearby = _distance_filter(list(eonet.get("events", [])), latitude, longitude, radius_km)

    earthquake_events = []
    for row in usgs.get("events", []):
        try:
            event_lat = float(row.get("latitude"))
            event_lon = float(row.get("longitude"))
        except (TypeError, ValueError):
            continue
        earthquake_events.append({
            "source": "USGS",
            "type": "Earthquake",
            "event": row.get("place") or "Earthquake",
            "magnitude": row.get("magnitude"),
            "latitude": event_lat,
            "longitude": event_lon,
            "distance_km": round(haversine_km(latitude, longitude, event_lat, event_lon), 1),
            "time": row.get("time"),
            "url": row.get("detail_url"),
        })

    event_register = list(earthquake_events)
    for row in gdacs_nearby:
        event_register.append({
            "source": "GDACS",
            "type": row.get("event_type"),
            "event": row.get("name") or row.get("country") or "Disaster event",
            "magnitude": None,
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "distance_km": row.get("distance_km"),
            "time": row.get("from_date"),
            "url": row.get("url"),
        })
    for row in eonet_nearby:
        event_register.append({
            "source": "NASA EONET",
            "type": row.get("categories"),
            "event": row.get("title") or "Natural event",
            "magnitude": row.get("magnitude"),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "distance_km": row.get("distance_km"),
            "time": row.get("latest_date"),
            "url": row.get("api_link"),
        })
    event_register.sort(key=lambda row: float(row.get("distance_km") or 10**9))

    sources["gdacs"] = {**gdacs, "events": gdacs_nearby}
    sources["eonet"] = {**eonet, "events": eonet_nearby}

    source_health = []
    for key, source in sources.items():
        source_health.append({
            "source": key,
            "label": source.get("source", key),
            "mode": source.get("mode", "DEMO"),
            "stale": bool(source.get("stale", False)),
            "fetched_at": source.get("fetched_at") or source.get("warning_fetched_at") or source.get("rainfall_fetched_at"),
            "access_status": source.get("access_status"),
            "error": source.get("error") or "; ".join(source.get("errors", [])),
        })

    return {
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "source_health": source_health,
        "events": event_register,
        "scope": {"days": int(days), "radius_km": int(radius_km), "min_magnitude": float(min_magnitude)},
        "analytical_effect": "CONTEXT_ONLY",
    }
