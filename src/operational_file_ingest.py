"""Operator-upload parsing for operational habitation and relocation-site datasets."""
from __future__ import annotations

import io
import json
from typing import BinaryIO

import pandas as pd


def _name(uploaded) -> str:
    return str(getattr(uploaded, "name", "uploaded.csv") or "uploaded.csv")


def _read_bytes(uploaded) -> bytes:
    if hasattr(uploaded, "getvalue"):
        value = uploaded.getvalue()
    else:
        value = uploaded.read()
    if isinstance(value, str):
        return value.encode("utf-8")
    return bytes(value)


def _geojson_to_dataframe(raw: bytes) -> pd.DataFrame:
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except Exception as exc:
        raise ValueError("uploaded GeoJSON/JSON must be valid UTF-8 JSON") from exc

    if payload.get("type") != "FeatureCollection":
        raise ValueError("operational GeoJSON must be a FeatureCollection")
    features = payload.get("features") or []
    if not features:
        raise ValueError("operational GeoJSON contains no features")

    rows = []
    for index, feature in enumerate(features):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") != "Point":
            raise ValueError(f"operational feature {index} must use Point geometry")
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2:
            raise ValueError(f"operational feature {index} has invalid Point coordinates")
        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"operational feature {index} coordinates must be numeric") from exc

        properties = dict(feature.get("properties") or {})
        properties.setdefault("longitude", longitude)
        properties.setdefault("latitude", latitude)
        rows.append(properties)

    return pd.DataFrame(rows)


def read_operational_upload(uploaded) -> pd.DataFrame:
    """Read an operator upload as a dataframe.

    Supported formats:
    - CSV
    - GeoJSON/JSON FeatureCollection with Point features

    GeoJSON geometry supplies latitude/longitude only when those properties are
    not already present. Validation of IDs, population, capacity and provenance
    remains the responsibility of the operational dataset validators.
    """
    name = _name(uploaded).lower()
    raw = _read_bytes(uploaded)
    if name.endswith(".csv"):
        return pd.read_csv(io.BytesIO(raw))
    if name.endswith(".geojson") or name.endswith(".json"):
        return _geojson_to_dataframe(raw)
    raise ValueError("operational upload must be CSV, GeoJSON, or JSON")
