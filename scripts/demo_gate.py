"""Run a pre-presentation gate for the deterministic offline SIH demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.batch_relocation import plan_batch_relocation  # noqa: E402
from src.global_optimizer import optimize_relocation_flow  # noqa: E402
from src.hazard_model import SUPPORTED_HAZARDS, compute_hazard_components  # noqa: E402
from src.imd_context import normalize_warning_record  # noqa: E402
from src.pipeline import (  # noqa: E402
    DEMO_CITIES,
    calculate_summary,
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
)
from src.relocation import allocate_population, rank_shelters  # noqa: E402
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
    ROOT / "pages/7_Live_Data_Context.py",
]


def run_demo_gate() -> dict:
    missing_pages = [str(path) for path in REQUIRED_PAGES if not path.exists()]
    if missing_pages:
        raise RuntimeError(f"required Streamlit pages are missing: {missing_pages}")

    # Offline parser smoke for the official IMD warning contract. No network is
    # required by the presentation gate.
    parsed_warning = normalize_warning_record(
        {"District": "Puri", "Day_1": "2,4", "Day1_Color": "2"}
    )
    if parsed_warning["day_1_level"] != "ORANGE" or "Heavy Rain" not in str(parsed_warning["day_1_warnings"]):
        raise RuntimeError("IMD warning normalization smoke test failed")

    habitations_raw, shelters_raw = load_demo_data()
    if not set(DEMO_CITIES).issubset(set(habitations_raw["demo_city"])):
        raise RuntimeError("multi-city demo does not contain all required cities")
    hazards = load_demo_hazards()

    profile_scores = {}
    for hazard_profile in SUPPORTED_HAZARDS:
        components = compute_hazard_components(habitations_raw, hazard_profile)
        if not components["hazard_score"].between(0, 100).all():
            raise RuntimeError(f"{hazard_profile} hazard model produced out-of-range scores")
        profile_scores[hazard_profile] = round(float(components["hazard_score"].mean()), 2)

    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type="combined")
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
    if habitations.empty or shelters.empty:
        raise RuntimeError("multi-city demo dataset is empty")
    if habitations["risk_score"].isna().any() or not habitations["risk_score"].between(0, 100).all():
        raise RuntimeError("risk scoring did not produce complete bounded scores")
    if shelters["available_capacity"].isna().any():
        raise RuntimeError("shelter capacity calculation did not complete")
    if not set(habitations["risk_level"]).issubset({"LOW", "MODERATE", "HIGH", "CRITICAL"}):
        raise RuntimeError("unexpected risk class produced")

    top = habitations.sort_values("risk_score", ascending=False).iloc[0].to_dict()
    local_shelters = shelters
    if top.get("demo_city") and "demo_city" in shelters.columns:
        local_shelters = shelters[shelters["demo_city"] == top["demo_city"]]
    shelter_records = local_shelters.to_dict(orient="records")
    ranked = rank_shelters(top, shelter_records)
    if not ranked:
        raise RuntimeError("no valid local shelter recommendation for the highest-risk habitation")
    relocation = ranked[0]
    if float(relocation.get("available_capacity", 0)) <= 0:
        raise RuntimeError("recommended shelter has no available capacity")

    allocation = allocate_population(top, shelter_records)
    required = int(allocation["required_population"])
    allocated = int(allocation["allocated_population"])
    deficit = int(allocation["remaining_deficit"])
    if allocated > required or allocated + deficit != required:
        raise RuntimeError("multi-shelter allocation violates population accounting")

    capacity_by_shelter = {str(candidate["shelter_id"]): int(candidate["available_capacity"]) for candidate in ranked}
    for item in allocation.get("allocations", []):
        if int(item["assigned_population"]) > capacity_by_shelter.get(str(item["shelter_id"]), 0):
            raise RuntimeError("allocation exceeds shelter available capacity")

    batch = plan_batch_relocation(habitations, shelters, priorities=("IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM"))
    if batch["allocated_population"] + batch["remaining_deficit"] != batch["required_population"]:
        raise RuntimeError("system-wide relocation plan violates population accounting")
    city_by_habitation = dict(zip(habitations["habitation_id"], habitations["demo_city"]))
    city_by_shelter = dict(zip(shelters["shelter_id"], shelters["demo_city"]))
    for item in batch["allocations"]:
        if city_by_habitation[item["habitation_id"]] != city_by_shelter[item["shelter_id"]]:
            raise RuntimeError("batch relocation crosses demo-city boundaries")

    optimized = optimize_relocation_flow(habitations, shelters, priorities=("IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM"))
    if optimized["allocated_population"] + optimized["remaining_deficit"] != optimized["required_population"]:
        raise RuntimeError("global optimizer violates population accounting")
    for item in optimized["allocations"]:
        if city_by_habitation[item["habitation_id"]] != city_by_shelter[item["shelter_id"]]:
            raise RuntimeError("global optimizer crosses demo-city boundaries")

    risk = calculate_risk(top)
    action_plan = generate_action_plan(habitation=top, risk=risk, relocation=relocation, allocation=allocation, data_mode="DEMO")
    required_report_text = ["Draft Disaster Response Action Plan", "Data mode: DEMO", "Risk Assessment", "Primary Relocation Recommendation", "Decision-support disclaimer"]
    if not all(text in action_plan for text in required_report_text):
        raise RuntimeError("draft action-plan export is incomplete")
    pdf_plan = generate_action_plan_pdf(habitation=top, risk=risk, relocation=relocation, allocation=allocation, data_mode="DEMO")
    if not pdf_plan.startswith(b"%PDF") or len(pdf_plan) < 1000:
        raise RuntimeError("PDF action-plan export is invalid")

    return {
        "demo_ready": True,
        "data_mode": "DEMO",
        "demo_cities": list(DEMO_CITIES),
        "hazard_profiles": list(SUPPORTED_HAZARDS),
        "hazard_profile_mean_scores": profile_scores,
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
        "global_optimizer": "PASS",
        "imd_warning_parser": "PASS",
        "action_plan_export": "PASS",
        "pdf_action_plan_export": "PASS",
        "required_pages": [str(path.relative_to(ROOT)) for path in REQUIRED_PAGES],
    }


if __name__ == "__main__":
    print(json.dumps(run_demo_gate(), indent=2))
