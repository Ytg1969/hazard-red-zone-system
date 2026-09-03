"""Configurable authority-data adapters for operational habitation/site feeds.

Configured HTTPS sources may return CSV or Point GeoJSON/JSON. A remote source
is never assumed authoritative merely because it is reachable: callers must
preserve source URL, LIVE/CACHED mode and validation results.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from src.live_data import fetch_text_with_cache
from src.operational_file_ingest import parse_operational_content
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters
from src.schema_mapping import apply_field_mapping
from src.url_safety import validate_public_https_url

# Existing names are preserved for deployment compatibility even though sources
# can now return either CSV or Point GeoJSON.
HABITATION_URL_ENV = "SIH_HABITATION_CSV_URL"
SHELTER_URL_ENV = "SIH_SHELTER_CSV_URL"
HABITATION_FIELD_MAP_ENV = "SIH_HABITATION_FIELD_MAP"
SHELTER_FIELD_MAP_ENV = "SIH_SHELTER_FIELD_MAP"


def _require_https(url: str) -> str:
    return validate_public_https_url(url, purpose="operational feed")


def _source_cache_path(kind: str, source_url: str) -> Path:
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:20]
    return Path("data/cache/operational") / f"{kind}_{digest}.json"


def configured_operational_urls() -> dict[str, str | None]:
    return {
        "habitations": os.getenv(HABITATION_URL_ENV),
        "shelters": os.getenv(SHELTER_URL_ENV),
    }


def configured_field_mapping(kind: str) -> dict[str, str]:
    env_name = HABITATION_FIELD_MAP_ENV if kind == "habitation" else SHELTER_FIELD_MAP_ENV
    raw = str(os.getenv(env_name, "") or "").strip()
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{env_name} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{env_name} must be a JSON object mapping canonical fields to source columns")
    return {str(key): str(value) for key, value in payload.items() if value not in {None, ""}}


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


def fetch_operational_habitations(url: str | None = None, *, cache_path: str | Path | None = None, field_mapping: dict[str, str] | None = None) -> dict:
    source_url = _require_https(url or os.getenv(HABITATION_URL_ENV) or "")
    resolved_cache = Path(cache_path) if cache_path is not None else _source_cache_path("habitations", source_url)
    envelope = fetch_text_with_cache(
        source="Configured habitation feed",
        url=source_url,
        cache_path=resolved_cache,
        timeout=12.0,
    )
    frame = _frame_from_envelope(envelope, source_url)
    mapping = field_mapping if field_mapping is not None else configured_field_mapping("habitation")
    if mapping:
        frame = apply_field_mapping(frame, mapping, "habitation")
    frame, assessment = normalize_operational_habitations(frame)
    frame = _apply_source_provenance(frame, envelope=envelope, source_url=source_url)
    return {
        "data": frame,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": source_url,
        "assessment": assessment,
        "field_mapping": mapping,
        "format": "geojson" if str(envelope.payload).lstrip().startswith("{") else "csv",
    }


def fetch_operational_shelters(url: str | None = None, *, cache_path: str | Path | None = None, field_mapping: dict[str, str] | None = None) -> dict:
    source_url = _require_https(url or os.getenv(SHELTER_URL_ENV) or "")
    resolved_cache = Path(cache_path) if cache_path is not None else _source_cache_path("shelters", source_url)
    envelope = fetch_text_with_cache(
        source="Configured shelter / relocation-site feed",
        url=source_url,
        cache_path=resolved_cache,
        timeout=12.0,
    )
    frame = _frame_from_envelope(envelope, source_url)
    mapping = field_mapping if field_mapping is not None else configured_field_mapping("shelter")
    if mapping:
        frame = apply_field_mapping(frame, mapping, "shelter")
    frame, assessment = normalize_operational_shelters(frame)
    frame = _apply_source_provenance(frame, envelope=envelope, source_url=source_url)
    return {
        "data": frame,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": source_url,
        "assessment": assessment,
        "field_mapping": mapping,
        "format": "geojson" if str(envelope.payload).lstrip().startswith("{") else "csv",
    }
