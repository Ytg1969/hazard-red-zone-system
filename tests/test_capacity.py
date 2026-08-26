from src.carrying_capacity import calculate_capacity


def test_limiting_resource_capacity():
    result = calculate_capacity({
        "total_capacity": 1500,
        "current_occupancy": 200,
        "water_capacity": 900,
        "sanitation_capacity": 1100,
        "access_capacity": 1200,
    })
    assert result["effective_capacity"] == 900.0
    assert result["available_capacity"] == 700.0


def test_available_capacity_never_negative():
    result = calculate_capacity({"total_capacity": 100, "current_occupancy": 150})
    assert result["available_capacity"] == 0.0
