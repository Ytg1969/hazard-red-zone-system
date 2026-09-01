"""Real-time situational-source orchestration for the EOC operations portal.

This module intentionally keeps external LIVE/CACHED context separate from the
frozen deterministic risk model. It provides one resilient call surface for UI
pages and future API/service layers while preserving explicit source status.
"""
from __future__ import annotations

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


def fetch_operations_snapshot(
    city: str,
    *,
    days: int = 7,
    radius_km: int = 500,
    min_magnitude: float = 2.5,
) -> dict:
    """Fetch an EOC-friendly snapshot for a verified demo-city coordinate.

    The result is situational context only. Nothing returned by this function is
    automatically mapped into H/E/V/A or the baseline risk score.
    """
    if city not in CITY_CENTERS:
        raise ValueError(f"operations snapshot requires one of {sorted(CITY_CENTERS)}")

    latitude, longitude = CITY_CENTERS[city]
    weather = _safe_call(
        "Open-Meteo Forecast API",
        lambda: fetch_weather_at_location(city, latitude, longitude),
    )
    air = _safe_call(
        "Open-Meteo Air Quality API",
        lambda: fetch_air_quality_at_location(city, latitude, longitude),
    )
    usgs = _safe_call(
        "USGS FDSN Earthquake Catalog",
        lambda: fetch_recent_earthquakes_at_location(
            city,
            latitude,
            longitude,
            days=days,
            radius_km=radius_km,
            min_magnitude=min_magnitude,
        ),
    )
    gdacs = _safe_call(
        "Global Disaster Alert and Coordination System (GDACS)",
        lambda: fetch_gdacs_events(days=days),
    )
    eonet = _safe_call(
        "NASA Earth Observatory Natural Event Tracker (EONET)",
        lambda: fetch_eonet_events(days=days, limit=100),
    )
    imd = _safe_call("India Meteorological Department (IMD)", lambda: fetch_imd_context(city))
    sachet = _safe_call("NDMA SACHET", fetch_disaster_alerts)

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

    sources = {
        "weather": weather,
        "air_quality": air,
        "usgs": usgs,
        "gdacs": {**gdacs, "events": gdacs_nearby},
        "eonet": {**eonet, "events": eonet_nearby},
        "imd": imd,
        "sachet": sachet,
    }
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
