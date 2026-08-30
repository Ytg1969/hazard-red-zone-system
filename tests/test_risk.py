import pytest

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
    assert sum(result["contributions"].values()) == 100.0


def test_zero_risk_is_low():
    result = calculate_risk({})
    assert result["risk_score"] == 0.0
    assert result["risk_level"] == "LOW"


def test_driver_order_uses_weighted_contribution():
    result = calculate_risk(
        {
            "hazard_score": 80,
            "exposure_score": 50,
            "vulnerability_score": 40,
            "accessibility_score": 100,
        }
    )
    # Hazard contributes 28 points; accessibility contributes 15.
    assert result["drivers"][0] == "hazard"


def test_invalid_weight_sum_is_rejected():
    with pytest.raises(ValueError, match="sum to 1.0"):
        calculate_risk(
            {},
            weights={
                "hazard": 0.5,
                "exposure": 0.5,
                "vulnerability": 0.5,
                "accessibility": 0.5,
            },
        )
