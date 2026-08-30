"""Run a lightweight pre-presentation gate for the offline SIH demo.

This check intentionally validates the deterministic DEMO path only. It does not
claim that the authoritative Puri pilot is complete.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.pipeline import (
    calculate_summary,
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
)


REQUIRED_PAGES = [
    Path("app.py"),
    Path("pages/1_Command_Center.py"),
    Path("pages/2_Red_Zone_Map.py"),
    Path("pages/3_Risk_Analysis.py"),
    Path("pages/4_Relocation_Planner.py"),
    Path("pages/5_Scenario_Studio.py"),
    Path("pages/6_Methodology.py"),
]


def run_demo_gate() -> dict:
    missing_pages = [str(path) for path in REQUIRED_PAGES if not path.exists()]
    if missing_pages:
        raise RuntimeError(f"required Streamlit pages are missing: {missing_pages}")

    habitations_raw, shelters_raw = load_demo_data()
    hazards = load_demo_hazards()
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards)
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)

    if habitations.empty:
        raise RuntimeError("demo habitation dataset is empty")
    if shelters.empty:
        raise RuntimeError("demo shelter dataset is empty")
    if "risk_score" not in habitations.columns or habitations["risk_score"].isna().any():
        raise RuntimeError("risk scoring did not produce complete scores")
    if "available_capacity" not in shelters.columns or shelters["available_capacity"].isna().any():
        raise RuntimeError("shelter capacity calculation did not complete")
    if not set(habitations["risk_level"]).issubset({"LOW", "MODERATE", "HIGH", "CRITICAL"}):
        raise RuntimeError("unexpected risk class produced")

    return {
        "demo_ready": True,
        "data_mode": "DEMO",
        "habitations": int(len(habitations)),
        "shelters": int(len(shelters)),
        "critical_red_zones": summary["critical_red_zones"],
        "population_at_risk": summary["population_at_risk"],
        "available_shelter_capacity": int(summary["available_shelter_capacity"]),
        "required_pages": [str(path) for path in REQUIRED_PAGES],
    }


if __name__ == "__main__":
    result = run_demo_gate()
    print(json.dumps(result, indent=2))
