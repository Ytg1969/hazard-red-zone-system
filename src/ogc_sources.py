"""Generic OGC source discovery for authority GIS services.

WMS/WFS discovery is context-only. A reachable layer is never treated as a
calibrated analytical hazard input until its legend/classes, reference period,
CRS and class-to-0–100 mapping are documented and reviewed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

from src.live_data import fetch_text_with_cache
from src.url_safety import validate_public_https_url

DEFAULT_CACHE_DIR = Path("data/cache/ogc")


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child_text(node: ET.Element, name: str) -> str | None:
    for child in node:
        if _local(child.tag) == name and child.text:
            value = child.text.strip()
            if value:
                return value
    return None


def _capabilities_url(base_url: str, service: str) -> str:
    raw = validate_public_https_url(base_url, purpose=f"{service} source")
    parsed = urlsplit(raw)
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params = {k: v for k, v in params.items() if k.lower() not in {"service", "request"}}
    params.update({"service": service, "request": "GetCapabilities"})
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(params), parsed.fragment))


def build_wms_capabilities_url(base_url: str) -> str:
    return _capabilities_url(base_url, "WMS")


def build_wfs_capabilities_url(base_url: str) -> str:
    return _capabilities_url(base_url, "WFS")


def parse_wms_capabilities(xml_text: str) -> dict:
    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        raise ValueError("WMS capabilities response is not valid XML") from exc
    root_name = _local(root.tag)
    if root_name not in {"WMS_Capabilities", "WMT_MS_Capabilities"}:
        raise ValueError(f"unexpected WMS capabilities root: {root_name}")
    version = root.attrib.get("version")
    service_title = None
    service_abstract = None
    layers: list[dict] = []
    for node in root.iter():
        if _local(node.tag) == "Service":
            service_title = _child_text(node, "Title") or service_title
            service_abstract = _child_text(node, "Abstract") or service_abstract
            break
    for node in root.iter():
        if _local(node.tag) != "Layer":
            continue
        name = _child_text(node, "Name")
        if not name:
            continue
        title = _child_text(node, "Title") or name
        abstract = _child_text(node, "Abstract")
        crs = []
        bbox = None
        for child in node:
            local = _local(child.tag)
            if local in {"CRS", "SRS"} and child.text:
                crs.extend(value for value in child.text.split() if value)
            elif local == "EX_GeographicBoundingBox":
                values = {}
                for item in child:
                    if item.text:
                        try:
                            values[_local(item.tag)] = float(item.text)
                        except ValueError:
                            pass
                required = {"westBoundLongitude", "eastBoundLongitude", "southBoundLatitude", "northBoundLatitude"}
                if required.issubset(values):
                    bbox = {"west": values["westBoundLongitude"], "east": values["eastBoundLongitude"], "south": values["southBoundLatitude"], "north": values["northBoundLatitude"]}
        layers.append({"name": name, "title": title, "abstract": abstract, "crs": sorted(set(crs)), "geographic_bbox": bbox})
    if not layers:
        raise ValueError("WMS capabilities contains no named layers")
    return {"version": version, "service_title": service_title or "WMS service", "service_abstract": service_abstract, "layers": layers, "layer_count": len(layers)}


def parse_wfs_capabilities(xml_text: str) -> dict:
    try:
        root = ET.fromstring(xml_text)
    except Exception as exc:
        raise ValueError("WFS capabilities response is not valid XML") from exc
    root_name = _local(root.tag)
    if root_name != "WFS_Capabilities":
        raise ValueError(f"unexpected WFS capabilities root: {root_name}")
    version = root.attrib.get("version")
    service_title = None
    service_abstract = None
    feature_types: list[dict] = []
    for node in root.iter():
        if _local(node.tag) in {"ServiceIdentification", "Service"}:
            service_title = _child_text(node, "Title") or service_title
            service_abstract = _child_text(node, "Abstract") or service_abstract
            if service_title:
                break
    for node in root.iter():
        if _local(node.tag) != "FeatureType":
            continue
        name = _child_text(node, "Name")
        if not name:
            continue
        title = _child_text(node, "Title") or name
        abstract = _child_text(node, "Abstract")
        default_crs = _child_text(node, "DefaultCRS") or _child_text(node, "DefaultSRS")
        other_crs = []
        bbox = None
        for child in node:
            local = _local(child.tag)
            if local in {"OtherCRS", "OtherSRS"} and child.text:
                other_crs.append(child.text.strip())
            elif local == "WGS84BoundingBox":
                lower = _child_text(child, "LowerCorner")
                upper = _child_text(child, "UpperCorner")
                try:
                    if lower and upper:
                        west, south = [float(v) for v in lower.split()[:2]]
                        east, north = [float(v) for v in upper.split()[:2]]
                        bbox = {"west": west, "south": south, "east": east, "north": north}
                except Exception:
                    bbox = None
        crs = [value for value in [default_crs, *other_crs] if value]
        feature_types.append({"name": name, "title": title, "abstract": abstract, "crs": sorted(set(crs)), "geographic_bbox": bbox})
    if not feature_types:
        raise ValueError("WFS capabilities contains no named feature types")
    return {"version": version, "service_title": service_title or "WFS service", "service_abstract": service_abstract, "feature_types": feature_types, "feature_type_count": len(feature_types)}


def _cache_path(url: str, prefix: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return DEFAULT_CACHE_DIR / f"{prefix}_{digest}.json"


def inspect_wms_source(base_url: str, *, timeout: float = 15.0) -> dict:
    capabilities_url = build_wms_capabilities_url(base_url)
    envelope = fetch_text_with_cache(source="OGC WMS capabilities", url=capabilities_url, cache_path=_cache_path(capabilities_url, "wms"), timeout=timeout)
    parsed = parse_wms_capabilities(str(envelope.payload))
    return {**parsed, "mode": envelope.mode, "stale": envelope.stale, "fetched_at": envelope.fetched_at, "source_url": capabilities_url, "analytical_effect": "CONTEXT_ONLY_UNTIL_CALIBRATED"}


def inspect_wfs_source(base_url: str, *, timeout: float = 15.0) -> dict:
    capabilities_url = build_wfs_capabilities_url(base_url)
    envelope = fetch_text_with_cache(source="OGC WFS capabilities", url=capabilities_url, cache_path=_cache_path(capabilities_url, "wfs"), timeout=timeout)
    parsed = parse_wfs_capabilities(str(envelope.payload))
    return {**parsed, "mode": envelope.mode, "stale": envelope.stale, "fetched_at": envelope.fetched_at, "source_url": capabilities_url, "analytical_effect": "CONTEXT_ONLY_UNTIL_CALIBRATED"}


def build_wfs_geojson_url(base_url: str, type_name: str, *, count: int | None = None) -> str:
    raw = validate_public_https_url(base_url, purpose="WFS source")
    parsed = urlsplit(raw)
    if not str(type_name or "").strip():
        raise ValueError("WFS type name is required")
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params = {k: v for k, v in params.items() if k.lower() not in {"service", "request", "typenames", "typename", "outputformat", "count"}}
    params.update({"service": "WFS", "request": "GetFeature", "typeNames": str(type_name).strip(), "outputFormat": "application/json"})
    if count is not None:
        params["count"] = str(max(1, int(count)))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(params), parsed.fragment))
