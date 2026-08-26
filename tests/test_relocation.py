from src.relocation import recommend_shelter


def test_recommendation_filters_unsafe_and_full_shelters():
    habitation = {"latitude": 20.27, "longitude": 85.84}
    shelters = [
        {"shelter_id": "BAD", "name": "Unsafe", "latitude": 20.28, "longitude": 85.85, "total_capacity": 500, "current_occupancy": 0, "safety_score": 20},
        {"shelter_id": "GOOD", "name": "Safe", "latitude": 20.29, "longitude": 85.86, "total_capacity": 500, "current_occupancy": 100, "safety_score": 90},
    ]
    result = recommend_shelter(habitation, shelters)
    assert result is not None
    assert result["shelter_id"] == "GOOD"
