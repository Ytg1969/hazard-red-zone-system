"""Offline-safe production readiness checks for SIH26191.

This script deliberately avoids requiring live network access. It verifies the
contracts that must remain true even when every external source is unavailable.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.provenance import default_provenance_register
from src.risk_engine import DEFAULT_WEIGHTS

REQUIRED_PAGES = [
    "app.py",
    "pages/0_Operations_Hub.py",
    "pages/1_Command_Center.py",
    "pages/2_Red_Zone_Map.py",
    "pages/3_Risk_Analysis.py",
    "pages/4_Relocation_Planner.py",
    "pages/5_Scenario_Studio.py",
    "pages/6_Methodology.py",
    "pages/7_Live_Data_Context.py",
    "pages/8_System_Readiness.py",
]


def run_gate() -> dict:
    result: dict = {"checks": {}}

    result["checks"]["risk_weights"] = {
        "pass": DEFAULT_WEIGHTS == {"hazard": 0.35, "exposure": 0.25, "vulnerability": 0.25, "accessibility": 0.15},
        "value": DEFAULT_WEIGHTS,
    }

    missing_pages = [path for path in REQUIRED_PAGES if not Path(path).exists()]
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

    result["production_ready_offline"] = all(check["pass"] for check in result["checks"].values())
    return result


if __name__ == "__main__":
    outcome = run_gate()
    print(json.dumps(outcome, indent=2, default=str))
    raise SystemExit(0 if outcome["production_ready_offline"] else 1)
