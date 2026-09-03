"""Offline-safe production readiness checks for SIH26191.

This script deliberately avoids requiring live network access. It verifies the
contracts that must remain true even when every external source is unavailable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.live_alerts import fetch_disaster_alerts  # noqa: E402
from src.ogc_sources import parse_wms_capabilities  # noqa: E402
from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards  # noqa: E402
from src.provenance import default_provenance_register  # noqa: E402
from src.risk_engine import DEFAULT_WEIGHTS  # noqa: E402

REQUIRED_PAGES = [
    ROOT / "app.py",
    ROOT / "pages/0_Operations_Hub.py",
    ROOT / "pages/1_Command_Center.py",
    ROOT / "pages/2_Red_Zone_Map.py",
    ROOT / "pages/3_Risk_Analysis.py",
    ROOT / "pages/4_Relocation_Planner.py",
    ROOT / "pages/5_Scenario_Studio.py",
    ROOT / "pages/6_Methodology.py",
    ROOT / "pages/7_Live_Data_Context.py",
    ROOT / "pages/8_System_Readiness.py",
    ROOT / "pages/9_Operational_Data.py",
    ROOT / "pages/10_GIS_Source_Inspector.py",
    ROOT / "pages/11_Calibrated_Hazard_Source.py",
    ROOT / "pages/12_Schema_Mapper.py",
]

_WMS_SAMPLE = """<WMS_Capabilities version='1.3.0' xmlns='http://www.opengis.net/wms'>
<Service><Title>Gate WMS</Title></Service><Capability><Layer><Title>Root</Title>
<Layer><Name>hazard</Name><Title>Hazard</Title><CRS>EPSG:4326</CRS></Layer>
</Layer></Capability></WMS_Capabilities>"""


def run_gate() -> dict:
    result: dict = {"checks": {}}

    result["checks"]["risk_weights"] = {
        "pass": DEFAULT_WEIGHTS == {"hazard": 0.35, "exposure": 0.25, "vulnerability": 0.25, "accessibility": 0.15},
        "value": DEFAULT_WEIGHTS,
    }

    missing_pages = [str(path.relative_to(ROOT)) for path in REQUIRED_PAGES if not path.exists()]
    result["checks"]["required_pages"] = {"pass": not missing_pages, "missing": missing_pages}

    habitations_raw, shelters_raw = load_demo_data()
    hazards = load_demo_hazards()
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type="combined")
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)

    result["checks"]["demo_pipeline"] = {
        "pass": bool(len(habitations) and len(shelters)),
        "habitations": len(habitations),
        "shelters": len(shelters),
        "population_at_risk": summary["population_at_risk"],
        "available_shelter_capacity": summary["available_shelter_capacity"],
    }

    no_overfill = bool((shelters["available_capacity"] >= 0).all())
    result["checks"]["nonnegative_available_capacity"] = {"pass": no_overfill}

    provenance = default_provenance_register()
    external_risk_mutators = [
        row for row in provenance
        if row["source"] in {"Open-Meteo", "Open-Meteo Air Quality", "USGS FDSN", "GDACS", "NASA EONET", "NRSC/ISRO Bhuvan WMS"}
        and row["affects_risk"]
    ]
    result["checks"]["live_context_isolation"] = {
        "pass": not external_risk_mutators,
        "violations": external_risk_mutators,
    }

    parsed_wms = parse_wms_capabilities(_WMS_SAMPLE)
    result["checks"]["ogc_discovery_parser"] = {
        "pass": parsed_wms.get("layer_count") == 1 and parsed_wms["layers"][0]["name"] == "hazard",
        "layer_count": parsed_wms.get("layer_count"),
    }

    # Ensure an unconfigured official-alert source does not fabricate current-looking rows.
    import os
    previous = os.environ.pop("SIH_SACHET_FEED_URL", None)
    try:
        sachet = fetch_disaster_alerts()
    finally:
        if previous is not None:
            os.environ["SIH_SACHET_FEED_URL"] = previous
    result["checks"]["sachet_unconfigured_is_empty"] = {
        "pass": sachet.get("access_status") == "UNCONFIGURED" and sachet.get("alerts") == [],
        "access_status": sachet.get("access_status"),
    }

    result["production_ready_offline"] = all(check["pass"] for check in result["checks"].values())
    return result


if __name__ == "__main__":
    outcome = run_gate()
    print(json.dumps(outcome, indent=2, default=str))
    raise SystemExit(0 if outcome["production_ready_offline"] else 1)
