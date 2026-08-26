import pandas as pd

from src.carrying_capacity import calculate_capacity
from src.risk_engine import calculate_risk
from src.vulnerability import calculate_vulnerability


def test_demo_pipeline_runs():
    habitations = pd.read_csv("data/demo/habitations.csv")
    shelters = pd.read_csv("data/demo/shelters.csv")

    habitation = habitations.iloc[0].to_dict()
    habitation.update(calculate_vulnerability(habitation))
    risk = calculate_risk(habitation)
    assert 0 <= risk["risk_score"] <= 100
    assert risk["risk_level"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}

    capacity = calculate_capacity(shelters.iloc[0].to_dict())
    assert capacity["available_capacity"] >= 0
