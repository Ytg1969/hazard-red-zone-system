"""Configurable authority-data adapters for operational habitation/site feeds.

Configured HTTPS sources may return CSV or Point GeoJSON/JSON. A remote source
is never assumed authoritative merely because it is reachable: callers must
preserve source URL, LIVE/CACHED mode and validation results.
"""
from __future__ import annotations

import os
from pathlib import Path

from src.live_data import fetch_text_with_cache
from src.operational_file_ingest import parse_operational_content
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters

# Existing names are preserved for deployment compatibility even though sources
# can now return either CSV or Point GeoJSON.
HABITATION_URL_ENV = "SIH_HABITATION_CSV_URL"
SHELTER_URL_ENV = "SIH_SHELTER_CSV_URL"


def _require_https(url: str) -> str:
    value = str(url or "").strip()
    if not value.lower().startswith("https://"):
        raise ValueError("operational feed URL must use HTTPS")
    return value


def configured_operational_urls() -> dict[str, str | None]:
    return {
        "habitations": os.getenv(HABITATION_URL_ENV),
        "shelters": os.getenv(SHELTER_URL_ENV),
    }


def _frame_from_envelope(envelope, source_url: str):
    return parse_operational_content(str(envelope.payload), source_name=source_url)


def _apply_source_provenance(frame, *, envelope, source_url: str):
    frame = frame.copy()
    frame["data_mode"] = envelope.mode
    if "data_timestamp" not in frame.columns:
        frame["data_timestamp"] = envelope.fetched_at
    if "source_context" not in frame.columns:
        frame["source_context"] = source_url
    return frame


def fetch_operational_habitations(url: str | None = None, *, cache_path: str | Path = "data/cache/operational/habitations.json") -> dict:
    source_url = _require_https(url or os.getenv(HABITATION_URL_ENV) or "")
    envelope = fetch_text_with_cache(
        source="Configured habitation feed",
        url=source_url,
        cache_path=cache_path,
        timeout=12.0,
    )
    frame, assessment = normalize_operational_habitations(_frame_from_envelope(envelope, source_url))
    frame = _apply_source_provenance(frame, envelope=envelope, source_url=source_url)
    return {
        "data": frame,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": source_url,
        "assessment": assessment,
        "format": "geojson" if str(envelope.payload).lstrip().startswith("{") else "csv",
    }


def fetch_operational_shelters(url: str | None = None, *, cache_path: str | Path = "data/cache/operational/shelters.json") -> dict:
    source_url = _require_https(url or os.getenv(SHELTER_URL_ENV) or "")
    envelope = fetch_text_with_cache(
        source="Configured shelter / relocation-site feed",
        url=source_url,
        cache_path=cache_path,
        timeout=12.0,
    )
    frame, assessment = normalize_operational_shelters(_frame_from_envelope(envelope, source_url))
    frame = _apply_source_provenance(frame, envelope=envelope, source_url=source_url)
    return {
        "data": frame,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": source_url,
        "assessment": assessment,
        "format": "geojson" if str(envelope.payload).lstrip().startswith("{") else "csv",
    }
