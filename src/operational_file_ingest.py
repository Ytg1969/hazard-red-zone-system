"""Parsing helpers for operational habitation and relocation-site datasets."""
from __future__ import annotations

import io
import json

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
        raise ValueError("operational GeoJSON/JSON must be valid UTF-8 JSON") from exc

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


def parse_operational_content(content: str | bytes, *, source_name: str = "operational.csv") -> pd.DataFrame:
    """Parse CSV or Point GeoJSON from uploads or configured HTTPS sources.

    Remote authority download endpoints often have no file extension, so payload
    content is used as a fallback signal. Operator uploads are stricter and are
    validated by ``read_operational_upload`` before reaching this helper.
    """
    raw = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    name = str(source_name or "").lower().split("?", 1)[0]
    stripped = raw.lstrip()

    if name.endswith(".geojson") or name.endswith(".json") or stripped.startswith(b"{"):
        return _geojson_to_dataframe(raw)

    try:
        return pd.read_csv(io.BytesIO(raw))
    except Exception as csv_exc:
        if stripped.startswith(b"{"):
            return _geojson_to_dataframe(raw)
        raise ValueError("operational source could not be parsed as CSV or Point GeoJSON") from csv_exc


def read_operational_upload(uploaded) -> pd.DataFrame:
    """Read an operator upload as CSV or Point GeoJSON/JSON.

    Unlike remote configured URLs, browser uploads must use an explicit supported
    filename extension so accidental XLSX/ZIP/binary uploads are never treated as
    permissive CSV input.
    """
    name = _name(uploaded).lower().split("?", 1)[0]
    if not name.endswith((".csv", ".geojson", ".json")):
        raise ValueError("operational upload must be CSV, GeoJSON, or JSON")
    return parse_operational_content(_read_bytes(uploaded), source_name=name)
