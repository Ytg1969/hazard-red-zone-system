from src.risk_engine import calculate_risk


def test_risk_boundaries_and_output():
    result = calculate_risk({
        "hazard_score": 100,
        "exposure_score": 100,
        "vulnerability_score": 100,
        "accessibility_score": 100,
    })
    assert result["risk_score"] == 100.0
    assert result["risk_level"] == "CRITICAL"


def test_zero_risk_is_low():
    result = calculate_risk({})
    assert result["risk_score"] == 0.0
    assert result["risk_level"] == "LOW"
