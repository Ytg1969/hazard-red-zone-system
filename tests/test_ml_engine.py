import pandas as pd
import pytest

from src.ml_engine import train_validation_model


def test_ml_engine_requires_minimum_records():
    data = pd.DataFrame(
        {
            "hazard_score": [10, 90],
            "exposure_score": [10, 90],
            "vulnerability_score": [10, 90],
            "accessibility_score": [10, 90],
            "affected": [0, 1],
        }
    )
    with pytest.raises(ValueError, match="at least 20"):
        train_validation_model(data, target_column="affected")


def test_ml_engine_trains_on_unit_test_fixture_only():
    # Synthetic fixture validates code behavior only; it is not scientific evidence.
    rows = []
    for i in range(40):
        high = i >= 20
        rows.append(
            {
                "hazard_score": 80 + (i % 10) if high else 10 + (i % 10),
                "exposure_score": 70 + (i % 10) if high else 20 + (i % 10),
                "vulnerability_score": 60 + (i % 10) if high else 15 + (i % 10),
                "accessibility_score": 65 + (i % 10) if high else 25 + (i % 10),
                "affected": 1 if high else 0,
            }
        )
    result = train_validation_model(pd.DataFrame(rows), target_column="affected")
    assert 0 <= result["metrics"]["accuracy"] <= 1
    assert set(result["feature_importance"]) == {
        "hazard_score",
        "exposure_score",
        "vulnerability_score",
        "accessibility_score",
    }
