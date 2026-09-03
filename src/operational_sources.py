"""Configurable authority-data adapters for operational habitation/site feeds.

Configured HTTPS sources may return CSV, XLSX, or Point GeoJSON/JSON. A remote
source is never assumed authoritative merely because it is reachable: callers
must preserve source URL, LIVE/CACHED mode and validation results.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse

from src.live_data import fetch_bytes_with_cache, fetch_text_with_cache
from src.operational_file_ingest import parse_operational_content
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters
from src.schema_mapping import apply_field_mapping
from src.url_safety import validate_public_https_url

# Existing names are preserved for deployment compatibility even though sources
# can return CSV, XLSX, or Point GeoJSON.
HABITATION_URL_ENV = "SIH_HABITATION_CSV_URL"
SHELTER_URL_ENV = "SIH_SHELTER_CSV_URL"
HABITATION_FIELD_MAP_ENV = "SIH_HABITATION_FIELD_MAP"
SHELTER_FIELD_MAP_ENV = "SIH_SHELTER_FIELD_MAP"


def _require_https(url: str) -> str:
    return validate_public_https_url(url, purpose="operational feed")


def _source_cache_path(kind: str, source_url: str, *, binary: bool = False) -> Path:
    digest = hashlib.sha256(source_url.encode("utf-8")).hexdigest()[:20]
    suffix = ".bin" if binary else ".json"
    return Path("data/cache/operational") / f"{kind}_{digest}{suffix}"


def _is_xlsx_url(source_url: str) -> bool:
    return urlparse(source_url).path.lower().endswith(".xlsx")


def _format_for(source_url: str, payload) -> str:
    if _is_xlsx_url(source_url):
        return "xlsx"
    if isinstance(payload, str) and payload.lstrip().startswith("{"):
        return "geojson"
    if isinstance(payload, (bytes, bytearray)) and bytes(payload).lstrip().startswith(b"{"):
        return "geojson"
    return "csv"


def _fetch_source_envelope(*, source: str, source_url: str, cache_path: str | Path | None, kind: str):
    is_xlsx = _is_xlsx_url(source_url)
    resolved_cache = Path(cache_path) if cache_path is not None else _source_cache_path(kind, source_url, binary=is_xlsx)
    fetcher = fetch_bytes_with_cache if is_xlsx else fetch_text_with_cache
    return fetcher(source=source, url=source_url, cache_path=resolved_cache, timeout=12.0)


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
    return parse_operational_content(envelope.payload, source_name=source_url)


def fetch_operational_preview(url: str, *, cache_path: str | Path | None = None) -> dict:
    """Fetch a public authority source without applying schema semantics.

    CSV, explicit `.xlsx`, and Point GeoJSON/JSON are supported. This adapter is
    only for schema discovery: it does not rename fields, certify authority, add
    analytical provenance, or run habitation/shelter production validation.
    """
    source_url = _require_https(url)
    envelope = _fetch_source_envelope(
        source="Operational schema preview",
        source_url=source_url,
        cache_path=cache_path,
        kind="preview",
    )
    frame = _frame_from_envelope(envelope, source_url)
    return {
        "data": frame,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": source_url,
        "format": _format_for(source_url, envelope.payload),
    }


def _apply_source_provenance(frame, *, envelope, source_url: str):
    """Attach transport provenance without inventing an observation timestamp."""
    frame = frame.copy()
    frame["data_mode"] = envelope.mode
    frame["source_fetched_at"] = envelope.fetched_at
    if "source_context" not in frame.columns:
        frame["source_context"] = source_url
    return frame


def fetch_operational_habitations(url: str | None = None, *, cache_path: str | Path | None = None, field_mapping: dict[str, str] | None = None) -> dict:
    source_url = _require_https(url or os.getenv(HABITATION_URL_ENV) or "")
    envelope = _fetch_source_envelope(
        source="Configured habitation feed", source_url=source_url, cache_path=cache_path, kind="habitations"
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
        "format": _format_for(source_url, envelope.payload),
    }


def fetch_operational_shelters(url: str | None = None, *, cache_path: str | Path | None = None, field_mapping: dict[str, str] | None = None) -> dict:
    source_url = _require_https(url or os.getenv(SHELTER_URL_ENV) or "")
    envelope = _fetch_source_envelope(
        source="Configured shelter / relocation-site feed", source_url=source_url, cache_path=cache_path, kind="shelters"
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
        "format": _format_for(source_url, envelope.payload),
    }
