"""Quick connectivity probe for verified external context sources.

This script is optional and internet-dependent. It never changes risk scores or
writes authoritative pilot data. It only reports LIVE/CACHED/DEMO availability.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.earthquake_context import fetch_recent_earthquakes  # noqa: E402
from src.imd_context import fetch_imd_context  # noqa: E402
from src.live_alerts import fetch_disaster_alerts  # noqa: E402


def probe() -> dict:
    cities = {}
    for city in ("Puri", "Guwahati", "Chennai"):
        imd = fetch_imd_context(city, timeout=5.0)
        try:
            usgs = fetch_recent_earthquakes(city, days=30, radius_km=500, min_magnitude=2.5)
            usgs_summary = {
                "mode": usgs["mode"],
                "events": len(usgs.get("events", [])),
                "stale": bool(usgs.get("stale")),
            }
        except Exception as exc:
            usgs_summary = {"mode": "DEMO", "events": 0, "error": str(exc)}

        cities[city] = {
            "imd": {
                "mode": imd["mode"],
                "warnings": len(imd.get("warnings", [])),
                "rainfall_rows": len(imd.get("rainfall", [])),
                "stale": bool(imd.get("stale")),
                "errors": imd.get("errors", []),
            },
            "usgs": usgs_summary,
        }

    sachet = fetch_disaster_alerts()
    return {
        "cities": cities,
        "sachet": {
            "mode": sachet["mode"],
            "alerts": len(sachet.get("alerts", [])),
            "stale": bool(sachet.get("stale")),
            "configured": sachet["mode"] != "DEMO",
        },
        "note": "External context only; no live source is injected into risk scoring by this probe.",
    }


if __name__ == "__main__":
    print(json.dumps(probe(), indent=2))
