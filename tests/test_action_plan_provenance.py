from src.report_generator import generate_action_plan, generate_action_plan_pdf


def _inputs():
    habitation = {
        "name": "Village A",
        "habitation_id": "H1",
        "population": 100,
        "children_population": 20,
        "elderly_population": 10,
        "relocation_priority": "SHORT_TERM",
    }
    risk = {"risk_score": 61.0, "risk_level": "HIGH", "drivers": ["Hazard"]}
    relocation = {
        "shelter_name": "Site A",
        "distance_km": 5.0,
        "travel_time_min": 12.0,
        "routing_mode": "osrm_cached",
        "route_status": "ROAD_NETWORK_ROUTE",
        "route_note": "Cached OSRM road route.",
        "available_capacity": 300,
        "capacity_validation_status": "VALIDATED",
        "limiting_resource_label": "Water",
        "limiting_capacity": 400,
        "capacity_evidence_completeness_pct": 100.0,
        "capacity_utilization_pct": 25.0,
        "suitability_score": 80.0,
    }
    allocation = {"required_population": 100, "allocated_population": 100, "remaining_deficit": 0, "allocations": []}
    provenance = {
        "habitations": {
            "mode": "LIVE",
            "sources": ["https://authority.example/habitations"],
            "observation_timestamps": ["2026-09-01T00:00:00Z"],
            "fetch_timestamps": ["2026-09-03T10:00:00Z"],
        },
        "shelters": {
            "mode": "CACHED",
            "sources": ["District EOC inventory"],
            "observation_timestamps": ["2026-09-02T06:00:00Z"],
            "fetch_timestamps": ["2026-09-03T10:02:00Z"],
        },
        "hazard": {
            "label": "Reviewed flood hazard layer",
            "mode": "LIVE",
            "calibration_status": "Explicitly activated calibrated hazard source",
        },
    }
    return habitation, risk, relocation, allocation, provenance


def test_markdown_action_plan_preserves_source_and_timestamp_distinction():
    habitation, risk, relocation, allocation, provenance = _inputs()
    text = generate_action_plan(
        habitation=habitation,
        risk=risk,
        relocation=relocation,
        allocation=allocation,
        data_mode="LIVE",
        provenance=provenance,
    )
    assert "## Data Provenance" in text
    assert "https://authority.example/habitations" in text
    assert "2026-09-01T00:00:00Z" in text
    assert "2026-09-03T10:00:00Z" in text
    assert "Retrieval time is not treated as the source observation/reference time" in text
    assert "Reviewed flood hazard layer" in text


def test_pdf_action_plan_accepts_provenance_payload():
    habitation, risk, relocation, allocation, provenance = _inputs()
    pdf = generate_action_plan_pdf(
        habitation=habitation,
        risk=risk,
        relocation=relocation,
        allocation=allocation,
        data_mode="LIVE",
        provenance=provenance,
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
