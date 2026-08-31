import pandas as pd

from src.hazard_model import SUPPORTED_HAZARDS, compute_hazard_components
from src.pipeline import DEMO_CITIES, enrich_habitations, load_demo_data, load_demo_hazards


def test_multicity_demo_covers_three_real_geographies():
    habitations, shelters = load_demo_data()
    assert set(DEMO_CITIES).issubset(set(habitations["demo_city"]))
    assert set(DEMO_CITIES).issubset(set(shelters["demo_city"]))
    assert set(habitations["data_mode"]) == {"DEMO"}
    assert set(shelters["data_mode"]) == {"DEMO"}


def test_every_hazard_profile_produces_bounded_scores():
    habitations, _ = load_demo_data()
    for hazard in SUPPORTED_HAZARDS:
        components = compute_hazard_components(habitations, hazard)
        assert components["hazard_score"].between(0, 100).all()
        assert 0 < float(components.attrs["data_completeness"]) <= 100


def test_multi_hazard_profiles_feed_frozen_risk_classes():
    habitations, _ = load_demo_data("Guwahati")
    hazards = load_demo_hazards()
    for hazard in ["flood", "landslide", "earthquake", "combined"]:
        enriched = enrich_habitations(habitations, hazard_data=hazards, hazard_type=hazard)
        assert enriched["risk_score"].between(0, 100).all()
        assert set(enriched["risk_level"]).issubset({"LOW", "MODERATE", "HIGH", "CRITICAL"})
        assert enriched["coordination_zone"].notna().all()


def test_missing_indicators_reweight_instead_of_crashing():
    df = pd.DataFrame({"rainfall_deficit_score": [80.0], "heat_stress_score": [70.0]})
    result = compute_hazard_components(df, "drought")
    assert result["hazard_score"].between(0, 100).all()
    assert 0 < result.attrs["data_completeness"] < 100
