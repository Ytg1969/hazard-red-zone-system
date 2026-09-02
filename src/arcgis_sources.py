"""Safe discovery helpers for public ArcGIS REST authority sources.

This module only inspects metadata and constructs explicit public query URLs.
Reachability is not evidence of calibration or authority for analytical risk use.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from src.live_data import fetch_json_with_cache


def _require_https(url: str) -> str:
    value = str(url or "").strip()
    if not value.lower().startswith("https://"):
        raise ValueError("ArcGIS REST URL must use HTTPS")
    return value


def metadata_url(url: str) -> str:
    """Return an ArcGIS REST metadata URL with f=pjson."""
    value = _require_https(url)
    parts = urlsplit(value)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["f"] = "pjson"
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), urlencode(query), parts.fragment))


def _extent(payload: dict) -> dict | None:
    extent = payload.get("extent") or payload.get("fullExtent")
    if not isinstance(extent, dict):
        return None
    return {
        "xmin": extent.get("xmin"),
        "ymin": extent.get("ymin"),
        "xmax": extent.get("xmax"),
        "ymax": extent.get("ymax"),
        "spatial_reference": (extent.get("spatialReference") or {}).get("latestWkid")
        or (extent.get("spatialReference") or {}).get("wkid"),
    }


def parse_arcgis_metadata(payload: dict) -> dict:
    """Normalize ArcGIS FeatureServer/MapServer service or layer metadata."""
    if not isinstance(payload, dict):
        raise ValueError("ArcGIS metadata response must be a JSON object")
    if payload.get("error"):
        message = (payload.get("error") or {}).get("message") or "ArcGIS service returned an error"
        raise ValueError(message)

    layers = []
    for layer in payload.get("layers") or []:
        if isinstance(layer, dict):
            layers.append({
                "id": layer.get("id"),
                "name": layer.get("name"),
                "parent_layer_id": layer.get("parentLayerId"),
                "default_visibility": layer.get("defaultVisibility"),
            })

    fields = []
    for field in payload.get("fields") or []:
        if isinstance(field, dict):
            fields.append({
                "name": field.get("name"),
                "alias": field.get("alias"),
                "type": field.get("type"),
            })

    capabilities = str(payload.get("capabilities") or "")
    return {
        "name": payload.get("name") or payload.get("mapName") or payload.get("serviceDescription") or "ArcGIS REST source",
        "description": payload.get("description") or payload.get("serviceDescription") or payload.get("copyrightText"),
        "type": payload.get("type"),
        "geometry_type": payload.get("geometryType"),
        "capabilities": capabilities,
        "supports_query": "query" in capabilities.lower(),
        "max_record_count": payload.get("maxRecordCount"),
        "extent": _extent(payload),
        "layers": layers,
        "fields": fields,
        "layer_count": len(layers),
        "field_count": len(fields),
    }


def inspect_arcgis_source(
    url: str,
    *,
    cache_path: str | Path = "data/cache/arcgis/metadata.json",
) -> dict:
    source_url = metadata_url(url)
    envelope = fetch_json_with_cache(
        source="ArcGIS REST authority source",
        url=source_url,
        cache_path=cache_path,
        timeout=12.0,
    )
    parsed = parse_arcgis_metadata(envelope.payload)
    return {
        **parsed,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": source_url,
    }


def layer_url(service_url: str, layer_id: int | str) -> str:
    value = _require_https(service_url).split("?", 1)[0].rstrip("/")
    return f"{value}/{int(layer_id)}"


def geojson_query_url(layer_service_url: str, *, where: str = "1=1", out_fields: str = "*") -> str:
    """Build a public ArcGIS FeatureServer layer query returning GeoJSON.

    The caller must first verify that the layer advertises Query capability and
    confirm data ownership/licensing before using the output operationally.
    """
    value = _require_https(layer_service_url).split("?", 1)[0].rstrip("/")
    if not value.lower().endswith("/query"):
        value = f"{value}/query"
    query = urlencode({
        "where": where,
        "outFields": out_fields,
        "returnGeometry": "true",
        "f": "geojson",
    })
    return f"{value}?{query}"
