"""Run a pre-presentation gate for the deterministic offline SIH demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.batch_relocation import plan_batch_relocation  # noqa: E402
from src.pipeline import (  # noqa: E402
    calculate_summary,
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
)
from src.relocation import allocate_population, rank_shelters, recommend_shelter  # noqa: E402
from src.report_generator import generate_action_plan, generate_action_plan_pdf  # noqa: E402
from src.risk_engine import calculate_risk  # noqa: E402


REQUIRED_PAGES = [
    ROOT / "app.py",
    ROOT / "pages/1_Command_Center.py",
    ROOT / "pages/2_Red_Zone_Map.py",
    ROOT / "pages/3_Risk_Analysis.py",
    ROOT / "pages/4_Relocation_Planner.py",
    ROOT / "pages/5_Scenario_Studio.py",
    ROOT / "pages/6_Methodology.py",
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

    batch = plan_batch_relocation(habitations, shelters)
    if batch["allocated_population"] + batch["remaining_deficit"] != batch["required_population"]:
        raise RuntimeError("system-wide relocation plan violates population accounting")
    batch_by_shelter: dict[str, int] = {}
    for item in batch["allocations"]:
        shelter_id = str(item["shelter_id"])
        batch_by_shelter[shelter_id] = batch_by_shelter.get(shelter_id, 0) + int(
            item["assigned_population"]
        )
    all_capacity_by_shelter = {
        str(row["shelter_id"]): int(row["available_capacity"])
        for row in shelters.to_dict(orient="records")
    }
    for shelter_id, assigned in batch_by_shelter.items():
        if assigned > all_capacity_by_shelter.get(shelter_id, 0):
            raise RuntimeError("system-wide allocation double-books shelter capacity")

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

    pdf_plan = generate_action_plan_pdf(
        habitation=top,
        risk=risk,
        relocation=relocation,
        allocation=allocation,
        data_mode="DEMO",
    )
    if not pdf_plan.startswith(b"%PDF") or len(pdf_plan) < 1000:
        raise RuntimeError("PDF action-plan export is invalid")

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
        "batch_required_population": int(batch["required_population"]),
        "batch_allocated_population": int(batch["allocated_population"]),
        "batch_remaining_deficit": int(batch["remaining_deficit"]),
        "action_plan_export": "PASS",
        "pdf_action_plan_export": "PASS",
        "required_pages": [str(path.relative_to(ROOT)) for path in REQUIRED_PAGES],
    }


if __name__ == "__main__":
    print(json.dumps(run_demo_gate(), indent=2))
