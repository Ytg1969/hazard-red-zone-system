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


def test_ranked_shelters_return_suitability_score():
    habitation = {"latitude": 20.27, "longitude": 85.84, "population": 200}
    shelters = [
        {
            "shelter_id": "A",
            "name": "A",
            "latitude": 20.28,
            "longitude": 85.85,
            "total_capacity": 300,
            "current_occupancy": 0,
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
    assert ranked[0]["suitability_score"] >= ranked[1]["suitability_score"]


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
