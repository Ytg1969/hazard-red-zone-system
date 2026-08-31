"""Inspect official Bhuvan Flood WMS capabilities without changing risk scores.

Internet-dependent utility for the final integration sprint. It queries the
known NRSC/ISRO Bhuvan flood WMS service families and prints advertised layer
names/titles. The output must be reviewed before any layer is mapped into the
hazard engine; this script deliberately performs no scoring.
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SERVICES = {
    "Flood Hazard": "https://bhuvan-ras2.nrsc.gov.in/cgi-bin/hazard.exe",
    "Flood Annual Layers": "https://bhuvan-ras2.nrsc.gov.in/cgi-bin/flood.exe",
}


def _capabilities_url(base_url: str) -> str:
    return f"{base_url}?{urlencode({'SERVICE':'WMS','REQUEST':'GetCapabilities'})}"


def _local_name(tag: str) -> str:
    return tag.split('}', 1)[-1]


def parse_layers(xml_text: str) -> list[dict]:
    """Extract layer name/title pairs from a WMS capabilities document."""
    root = ET.fromstring(xml_text)
    layers: list[dict] = []
    for layer in root.iter():
        if _local_name(layer.tag) != "Layer":
            continue
        name = None
        title = None
        for child in list(layer):
            local = _local_name(child.tag)
            if local == "Name":
                name = (child.text or "").strip() or None
            elif local == "Title":
                title = (child.text or "").strip() or None
        if name:
            layers.append({"name": name, "title": title})
    return layers


def probe(timeout: float = 10.0) -> dict:
    output = {}
    for label, base_url in SERVICES.items():
        url = _capabilities_url(base_url)
        try:
            request = Request(url, headers={"User-Agent": "SIH26191/1.0"})
            with urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
            layers = parse_layers(text)
            output[label] = {
                "status": "OK",
                "service_url": base_url,
                "capabilities_url": url,
                "layer_count": len(layers),
                "layers": layers,
            }
        except Exception as exc:
            output[label] = {
                "status": "UNAVAILABLE",
                "service_url": base_url,
                "capabilities_url": url,
                "error": str(exc),
                "layers": [],
            }
    output["warning"] = (
        "Layer discovery is not scientific calibration. Verify coverage, CRS, legend/classes, "
        "reference period and source-class-to-0-100 mapping before analytical use."
    )
    return output


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
