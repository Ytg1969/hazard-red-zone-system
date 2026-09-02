"""Generic OGC source discovery for authority GIS services.

This module inspects WMS capabilities without treating a reachable layer as a
calibrated analytical hazard input. It is intended to help operators connect
Bhuvan, SDMA, district, or other accountable GIS services while preserving
source provenance and the frozen risk contract.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

from src.live_data import fetch_text_with_cache

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


def build_wms_capabilities_url(base_url: str) -> str:
    """Return an HTTPS WMS GetCapabilities URL while preserving vendor params."""
    raw = str(base_url or "").strip()
    parsed = urlsplit(raw)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError("WMS source must be an absolute HTTPS URL")
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    # Remove case variants before inserting canonical request parameters.
    params = {k: v for k, v in params.items() if k.lower() not in {"service", "request"}}
    params.update({"service": "WMS", "request": "GetCapabilities"})
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(params), parsed.fragment))


def parse_wms_capabilities(xml_text: str) -> dict:
    """Parse the useful, portable subset of WMS 1.1/1.3 capabilities."""
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
                    bbox = {
                        "west": values["westBoundLongitude"],
                        "east": values["eastBoundLongitude"],
                        "south": values["southBoundLatitude"],
                        "north": values["northBoundLatitude"],
                    }
        layers.append({
            "name": name,
            "title": title,
            "abstract": abstract,
            "crs": sorted(set(crs)),
            "geographic_bbox": bbox,
        })

    if not layers:
        raise ValueError("WMS capabilities contains no named layers")
    return {
        "version": version,
        "service_title": service_title or "WMS service",
        "service_abstract": service_abstract,
        "layers": layers,
        "layer_count": len(layers),
    }


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return DEFAULT_CACHE_DIR / f"wms_{digest}.json"


def inspect_wms_source(base_url: str, *, timeout: float = 15.0) -> dict:
    """Fetch and parse a WMS capabilities document with LIVE/CACHED semantics."""
    capabilities_url = build_wms_capabilities_url(base_url)
    envelope = fetch_text_with_cache(
        source="OGC WMS capabilities",
        url=capabilities_url,
        cache_path=_cache_path(capabilities_url),
        timeout=timeout,
    )
    parsed = parse_wms_capabilities(str(envelope.payload))
    return {
        **parsed,
        "mode": envelope.mode,
        "stale": envelope.stale,
        "fetched_at": envelope.fetched_at,
        "source_url": capabilities_url,
        "analytical_effect": "CONTEXT_ONLY_UNTIL_CALIBRATED",
    }
