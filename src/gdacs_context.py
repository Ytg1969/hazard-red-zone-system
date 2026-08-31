"""GDACS multi-hazard event context with LIVE→CACHED behavior.

GDACS is a UN/EU-supported global disaster-awareness service. Its API is used
here as supplemental situational context only; it does not alter the frozen
analytical risk score without an explicit calibrated mapping.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

from src.live_data import fetch_json_with_cache

GDACS_EVENTS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/SEARCH"


def _event_rows(payload) -> list[dict]:
    if isinstance(payload, dict):
        features = payload.get("features")
        if isinstance(features, list):
            rows = []
            for feature in features:
                if not isinstance(feature, dict):
                    continue
                props = dict(feature.get("properties") or {})
                geometry = feature.get("geometry") or {}
                coordinates = geometry.get("coordinates") or []
                if isinstance(coordinates, list) and len(coordinates) >= 2 and not isinstance(coordinates[0], list):
                    props.setdefault("longitude", coordinates[0])
                    props.setdefault("latitude", coordinates[1])
                rows.append(props)
            return rows
        for key in ("data", "results", "events"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    return []


def fetch_gdacs_events(*, days: int = 7, timeout: float = 8.0) -> dict:
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=max(1, int(days)))
    params = urlencode(
        {
            "eventlist": "EQ;TC;FL;DR;VO",
            "fromdate": start.strftime("%Y-%m-%d"),
            "todate": now.strftime("%Y-%m-%d"),
            "alertlevel": "green;orange;red",
        }
    )
    envelope = fetch_json_with_cache(
        source="Global Disaster Alert and Coordination System (GDACS)",
        url=f"{GDACS_EVENTS_URL}?{params}",
        cache_path=Path("data/cache/gdacs") / "recent_events.json",
        timeout=timeout,
    )
    rows = _event_rows(envelope.payload)
    normalized = []
    for row in rows:
        lowered = {str(key).lower(): value for key, value in row.items()}
        normalized.append(
            {
                "event_type": lowered.get("eventtype") or lowered.get("event_type") or lowered.get("type"),
                "event_id": lowered.get("eventid") or lowered.get("event_id") or lowered.get("id"),
                "name": lowered.get("name") or lowered.get("eventname") or lowered.get("title"),
                "country": lowered.get("country") or lowered.get("countryname"),
                "alert_level": lowered.get("alertlevel") or lowered.get("alert_level") or lowered.get("alertscore"),
                "severity": lowered.get("severity") or lowered.get("severitytext"),
                "from_date": lowered.get("fromdate") or lowered.get("from_date"),
                "to_date": lowered.get("todate") or lowered.get("to_date"),
                "latitude": lowered.get("latitude"),
                "longitude": lowered.get("longitude"),
                "url": lowered.get("url") or lowered.get("link"),
            }
        )
    return {
        "source": envelope.source,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": envelope.source_url,
        "events": normalized,
    }
