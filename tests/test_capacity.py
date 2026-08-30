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
    assert result["capacity_validation_status"] == "VALIDATED"


def test_partial_capacity_uses_known_constraints():
    result = calculate_capacity({
        "total_capacity": 1000,
        "current_occupancy": 100,
        "water_capacity": 800,
        "sanitation_capacity": "",
    })
    assert result["effective_capacity"] == 800.0
    assert result["available_capacity"] == 700.0
    assert result["capacity_validation_status"] == "PARTIAL"
    assert "sanitation_capacity" in result["missing_resource_fields"]
    assert "access_capacity" in result["missing_resource_fields"]


def test_total_capacity_fallback_is_unvalidated():
    result = calculate_capacity({"total_capacity": 500, "current_occupancy": 100})
    assert result["effective_capacity"] == 500.0
    assert result["available_capacity"] == 400.0
    assert result["capacity_validation_status"] == "UNVALIDATED"


def test_available_capacity_never_negative():
    result = calculate_capacity({"total_capacity": 100, "current_occupancy": 150})
    assert result["available_capacity"] == 0.0
