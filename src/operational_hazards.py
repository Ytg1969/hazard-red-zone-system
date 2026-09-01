"""Validation and reconstruction of operator-supplied calibrated GeoJSON hazard layers."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.live_data import fetch_text_with_cache

HAZARD_URL_ENV = "SIH_HAZARD_GEOJSON_URL"
HAZARD_CONFIRM_ENV = "SIH_HAZARD_CALIBRATION_CONFIRMED"
HAZARD_LABEL_ENV = "SIH_HAZARD_SOURCE_LABEL"
DEFAULT_HAZARD_CACHE = "data/cache/operational/hazard_geojson.json"


def validate_geojson_hazard(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except Exception as exc:
        raise ValueError("hazard file must be valid GeoJSON/JSON") from exc
    if payload.get("type") != "FeatureCollection":
        raise ValueError("hazard GeoJSON must be a FeatureCollection")
    features = payload.get("features") or []
    if not features:
        raise ValueError("hazard GeoJSON contains no features")
    for index, feature in enumerate(features):
        props = feature.get("properties") or {}
        if "hazard_score" not in props:
            raise ValueError(f"hazard feature {index} is missing hazard_score")
        try:
            score = float(props["hazard_score"])
        except Exception as exc:
            raise ValueError(f"hazard feature {index} hazard_score must be numeric") from exc
        if not 0 <= score <= 100:
            raise ValueError(f"hazard feature {index} hazard_score must be between 0 and 100")
        geometry = feature.get("geometry")
        if not geometry:
            raise ValueError(f"hazard feature {index} is missing geometry")
    return {"feature_count": len(features), "payload": payload}


def geojson_to_gdf(text: str):
    """Build a WGS84 GeoDataFrame lazily so non-GIS pages stay lightweight."""
    checked = validate_geojson_hazard(text)
    import geopandas as gpd

    gdf = gpd.GeoDataFrame.from_features(checked["payload"]["features"], crs="EPSG:4326")
    if gdf.empty:
        raise ValueError("hazard layer is empty")
    return gdf


def configured_hazard_source() -> dict[str, Any]:
    url = os.getenv(HAZARD_URL_ENV)
    confirmed = str(os.getenv(HAZARD_CONFIRM_ENV, "")).strip().lower() in {"1", "true", "yes", "confirmed"}
    return {
        "url": url,
        "calibration_confirmed": confirmed,
        "label": os.getenv(HAZARD_LABEL_ENV) or "Configured calibrated hazard GeoJSON",
    }


def fetch_configured_hazard(
    url: str | None = None,
    *,
    calibration_confirmed: bool | None = None,
    cache_path: str | Path = DEFAULT_HAZARD_CACHE,
) -> dict[str, Any]:
    """Fetch a deployment-configured calibrated hazard layer with LIVE/CACHED semantics.

    The feed is rejected unless the deployment explicitly confirms that its
    hazard_score mapping is documented and suitable for analytical use. This is
    intentionally stricter than merely checking that the URL is reachable.
    """
    configured = configured_hazard_source()
    source_url = str(url or configured["url"] or "").strip()
    if not source_url.lower().startswith("https://"):
        raise ValueError("configured hazard URL must use HTTPS")

    confirmed = configured["calibration_confirmed"] if calibration_confirmed is None else bool(calibration_confirmed)
    if not confirmed:
        raise ValueError("configured hazard feed is blocked until SIH_HAZARD_CALIBRATION_CONFIRMED=true")

    envelope = fetch_text_with_cache(
        source=str(configured["label"]),
        url=source_url,
        cache_path=cache_path,
        timeout=15.0,
    )
    text = str(envelope.payload)
    checked = validate_geojson_hazard(text)
    return {
        "geojson": text,
        "feature_count": checked["feature_count"],
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": source_url,
        "label": str(configured["label"]),
    }
