"""Validation and reconstruction of operator-supplied calibrated GeoJSON hazard layers."""
from __future__ import annotations

import json
from typing import Any


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
