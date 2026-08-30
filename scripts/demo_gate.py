"""Run a pre-presentation gate for the deterministic offline SIH demo.

This validates the full DEMO decision-support path without claiming that the
authoritative Puri pilot is complete.
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
from src.relocation import allocate_population, rank_shelters, recommend_shelter
from src.report_generator import generate_action_plan
from src.risk_engine import calculate_risk


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

    top = habitations.sort_values("risk_score", ascending=False).iloc[0].to_dict()
    shelter_records = shelters.to_dict(orient="records")
    ranked = rank_shelters(top, shelter_records)
    relocation = recommend_shelter(top, shelter_records)
    if relocation is None or not ranked:
        raise RuntimeError("no valid shelter recommendation for the highest-risk habitation")
    if float(relocation.get("available_capacity", 0)) <= 0:
        raise RuntimeError("recommended shelter has no available capacity")

    allocation = allocate_population(top, shelter_records)
    required = int(allocation["required_population"])
    allocated = int(allocation["allocated_population"])
    deficit = int(allocation["remaining_deficit"])
    if allocated > required or allocated + deficit != required:
        raise RuntimeError("multi-shelter allocation violates population accounting")

    capacity_by_shelter = {
        str(candidate["shelter_id"]): int(candidate["available_capacity"])
        for candidate in ranked
    }
    for item in allocation.get("allocations", []):
        shelter_id = str(item["shelter_id"])
        assigned = int(item["assigned_population"])
        if assigned > capacity_by_shelter.get(shelter_id, 0):
            raise RuntimeError("allocation exceeds shelter available capacity")

    risk = calculate_risk(top)
    action_plan = generate_action_plan(
        habitation=top,
        risk=risk,
        relocation=relocation,
        allocation=allocation,
        data_mode="DEMO",
    )
    required_report_text = [
        "Draft Disaster Response Action Plan",
        "Data mode: DEMO",
        "Risk Assessment",
        "Primary Relocation Recommendation",
        "Decision-support disclaimer",
    ]
    if not all(text in action_plan for text in required_report_text):
        raise RuntimeError("draft action-plan export is incomplete")

    return {
        "demo_ready": True,
        "data_mode": "DEMO",
        "habitations": int(len(habitations)),
        "shelters": int(len(shelters)),
        "critical_red_zones": summary["critical_red_zones"],
        "population_at_risk": summary["population_at_risk"],
        "available_shelter_capacity": int(summary["available_shelter_capacity"]),
        "sample_habitation": str(top["name"]),
        "sample_recommended_shelter": str(relocation["shelter_name"]),
        "sample_required_population": required,
        "sample_allocated_population": allocated,
        "sample_remaining_deficit": deficit,
        "action_plan_export": "PASS",
        "required_pages": [str(path) for path in REQUIRED_PAGES],
    }


if __name__ == "__main__":
    result = run_demo_gate()
    print(json.dumps(result, indent=2))
