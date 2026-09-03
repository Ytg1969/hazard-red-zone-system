import pandas as pd
import pytest

from src.relocation import allocate_population, rank_shelters, recommend_shelter


def test_recommendation_filters_unsafe_and_full_shelters():
    habitation = {"latitude": 20.27, "longitude": 85.84, "population": 300}
    shelters = [
        {
            "shelter_id": "BAD",
            "name": "Unsafe",
            "latitude": 20.28,
            "longitude": 85.85,
            "total_capacity": 500,
            "current_occupancy": 0,
            "safety_score": 20,
            "accessibility_score": 80,
        },
        {
            "shelter_id": "FULL",
            "name": "Full",
            "latitude": 20.281,
            "longitude": 85.851,
            "total_capacity": 100,
            "current_occupancy": 100,
            "safety_score": 95,
            "accessibility_score": 90,
        },
        {
            "shelter_id": "GOOD",
            "name": "Safe",
            "latitude": 20.29,
            "longitude": 85.86,
            "total_capacity": 500,
            "current_occupancy": 100,
            "safety_score": 90,
            "accessibility_score": 80,
        },
    ]
    result = recommend_shelter(habitation, shelters)
    assert result is not None
    assert result["shelter_id"] == "GOOD"


def test_ranked_shelters_return_suitability_and_capacity_evidence():
    habitation = {"latitude": 20.27, "longitude": 85.84, "population": 200}
    shelters = [
        {
            "shelter_id": "A",
            "name": "A",
            "latitude": 20.28,
            "longitude": 85.85,
            "total_capacity": 300,
            "current_occupancy": 0,
            "water_capacity": 250,
            "sanitation_capacity": 280,
            "access_capacity": 260,
            "safety_score": 85,
            "accessibility_score": 80,
        },
        {
            "shelter_id": "B",
            "name": "B",
            "latitude": 20.40,
            "longitude": 85.95,
            "total_capacity": 1000,
            "current_occupancy": 0,
            "safety_score": 90,
            "accessibility_score": 90,
        },
    ]
    ranked = rank_shelters(habitation, shelters)
    assert len(ranked) == 2
    assert all("suitability_score" in item for item in ranked)
    assert all("limiting_resource_label" in item for item in ranked)
    assert all("capacity_evidence_completeness_pct" in item for item in ranked)
    assert all("route_status" in item for item in ranked)
    assert ranked[0]["suitability_score"] >= ranked[1]["suitability_score"]
    candidate_a = next(item for item in ranked if item["shelter_id"] == "A")
    assert candidate_a["limiting_resource"] == "water_capacity"
    assert candidate_a["limiting_capacity"] == 250.0
    assert candidate_a["capacity_evidence_completeness_pct"] == 100.0
    assert candidate_a["routing_mode"] == "haversine_fallback"
    assert candidate_a["route_status"] == "STRAIGHT_LINE_FALLBACK"


def test_ranked_shelter_passes_live_routing_flag_and_preserves_route_provenance(monkeypatch):
    calls = []

    def fake_route(origin, destination, graphml_path=None, average_speed_kmph=30.0, *, allow_live_osrm=False):
        calls.append({
            "origin": origin,
            "destination": destination,
            "graphml_path": graphml_path,
            "allow_live_osrm": allow_live_osrm,
        })
        return {
            "distance_km": 12.3,
            "travel_time_min": 24.5,
            "routing_mode": "osrm_cached",
            "route_status": "ROAD_NETWORK_ROUTE",
            "route_note": "Cached OSRM road route.",
            "source_url": "https://router.project-osrm.org/example",
            "stale": True,
        }

    monkeypatch.setattr("src.relocation.estimate_route", fake_route)
    habitation = {"latitude": 20.27, "longitude": 85.84, "population": 100}
    shelters = [{
        "shelter_id": "A",
        "name": "A",
        "latitude": 20.30,
        "longitude": 85.90,
        "total_capacity": 500,
        "current_occupancy": 0,
        "safety_score": 90,
        "accessibility_score": 80,
    }]

    ranked = rank_shelters(habitation, shelters, graphml_path="roads.graphml", allow_live_routing=True)

    assert calls and calls[0]["allow_live_osrm"] is True
    assert calls[0]["graphml_path"] == "roads.graphml"
    assert ranked[0]["routing_mode"] == "osrm_cached"
    assert ranked[0]["route_status"] == "ROAD_NETWORK_ROUTE"
    assert ranked[0]["route_stale"] is True
    assert ranked[0]["travel_time_min"] == 24.5
    assert ranked[0]["route_source_url"].startswith("https://router.project-osrm.org")


def test_population_allocation_never_exceeds_available_capacity():
    habitation = {"latitude": 20.27, "longitude": 85.84, "population": 600}
    shelters = [
        {
            "shelter_id": "A",
            "name": "A",
            "latitude": 20.28,
            "longitude": 85.85,
            "total_capacity": 300,
            "current_occupancy": 0,
            "safety_score": 90,
            "accessibility_score": 80,
        },
        {
            "shelter_id": "B",
            "name": "B",
            "latitude": 20.29,
            "longitude": 85.86,
            "total_capacity": 250,
            "current_occupancy": 0,
            "safety_score": 90,
            "accessibility_score": 80,
        },
    ]
    result = allocate_population(habitation, shelters)
    assert result["allocated_population"] == 550
    assert result["remaining_deficit"] == 50
    assert sum(item["assigned_population"] for item in result["allocations"]) == 550


def test_relocation_accepts_dataframe_and_series_inputs():
    habitation = pd.Series(
        {"latitude": 20.27, "longitude": 85.84, "population": 200}
    )
    shelters = pd.DataFrame(
        [
            {
                "shelter_id": "A",
                "name": "A",
                "latitude": 20.28,
                "longitude": 85.85,
                "total_capacity": 300,
                "current_occupancy": 0,
                "safety_score": 85,
                "accessibility_score": 80,
            }
        ]
    )

    ranked = rank_shelters(habitation, shelters)
    recommendation = recommend_shelter(habitation, shelters)
    allocation = allocate_population(habitation, shelters)

    assert len(ranked) == 1
    assert recommendation is not None
    assert recommendation["shelter_id"] == "A"
    assert allocation["allocated_population"] == 200
    assert allocation["remaining_deficit"] == 0


def test_relocation_rejects_string_shelter_collection_with_clear_error():
    habitation = {"latitude": 20.27, "longitude": 85.84, "population": 200}
    with pytest.raises(TypeError, match="list of records or a DataFrame"):
        rank_shelters(habitation, "shelter-name")
