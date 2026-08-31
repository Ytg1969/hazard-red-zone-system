"""Verified Bhuvan WMS layer registry for contextual map overlays.

These layers were discovered from live WMS GetCapabilities responses. They are
historical/contextual GIS layers only and MUST NOT change the deterministic
risk score unless coverage, reference period, legend/classes, CRS and a
source-class-to-0-100 mapping are separately calibrated and documented.
"""
from __future__ import annotations

FLOOD_HAZARD_WMS = "https://bhuvan-ras2.nrsc.gov.in/cgi-bin/hazard.exe"
FLOOD_ANNUAL_WMS = "https://bhuvan-ras2.nrsc.gov.in/cgi-bin/flood.exe"

CITY_BHUVAN_LAYERS = {
    "Puri": [
        {
            "label": "Odisha Cyclone (historical/context)",
            "service_url": FLOOD_ANNUAL_WMS,
            "layer": "or_cyclone",
            "reference": "Bhuvan WMS advertised layer",
        },
        {
            "label": "Odisha Flood 29 Oct 2013 (historical)",
            "service_url": FLOOD_ANNUAL_WMS,
            "layer": "or_291013_flood",
            "reference": "Bhuvan WMS advertised layer",
        },
    ],
    "Guwahati": [
        {
            "label": "Assam Flood Hazard (authoritative context)",
            "service_url": FLOOD_HAZARD_WMS,
            "layer": "as_hz",
            "reference": "Bhuvan Flood Hazard WMS / Assam_Hazard",
        },
        {
            "label": "Assam Flood 19 Sep 2013 (historical)",
            "service_url": FLOOD_ANNUAL_WMS,
            "layer": "as_190913_flood",
            "reference": "Bhuvan WMS advertised layer",
        },
    ],
    "Chennai": [
        {
            "label": "Tamil Nadu Flood 1 Nov 2012 (historical)",
            "service_url": FLOOD_ANNUAL_WMS,
            "layer": "tn_011112_flood",
            "reference": "Bhuvan WMS advertised layer",
        },
    ],
}


def layers_for_city(city: str) -> list[dict]:
    """Return verified contextual Bhuvan layers for one demo city."""
    return list(CITY_BHUVAN_LAYERS.get(city, []))
