from src.pipeline import (
    calculate_summary,
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
)
from src.relocation import allocate_population, recommend_shelter


def test_demo_pipeline_runs_end_to_end():
    habitations_raw, shelters_raw = load_demo_data()
    hazards = load_demo_hazards()

    habitations = enrich_habitations(habitations_raw, hazard_data=hazards)
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)

    assert len(habitations) > 0
    assert len(shelters) > 0
    assert summary["habitations_monitored"] == len(habitations)
    assert habitations["risk_score"].between(0, 100).all()
    assert set(habitations["risk_level"]).issubset({"LOW", "MODERATE", "HIGH", "CRITICAL"})
    assert (shelters["available_capacity"] >= 0).all()

    habitation = habitations.sort_values("risk_score", ascending=False).iloc[0].to_dict()
    shelter_records = shelters.to_dict(orient="records")
    recommendation = recommend_shelter(habitation, shelter_records)
    assert recommendation is not None
    assert recommendation["available_capacity"] > 0

    allocation = allocate_population(habitation, shelter_records)
    assert allocation["allocated_population"] <= allocation["required_population"]
    assert allocation["remaining_deficit"] >= 0
