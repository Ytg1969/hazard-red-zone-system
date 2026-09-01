import pandas as pd

from src.operational_workspace import (
    dataset_mode,
    geographic_center,
    normalize_operational_habitations,
    normalize_operational_shelters,
    restore_workspace,
    serialize_workspace,
)


def _habitations():
    return pd.DataFrame([
        {"habitation_id": "H1", "name": "Village A", "latitude": 20.0, "longitude": 85.0, "population": 1000, "children_population": 180, "elderly_population": 90, "hazard_score": 70, "exposure_score": 65, "accessibility_score": 55, "data_mode": "LIVE", "data_timestamp": "2026-09-01T00:00:00Z", "source_context": "official-test"},
        {"habitation_id": "H2", "name": "Village B", "latitude": 20.2, "longitude": 85.2, "population": 800, "children_population": 130, "elderly_population": 70, "hazard_score": 55, "exposure_score": 50, "accessibility_score": 45, "data_mode": "LIVE", "data_timestamp": "2026-09-01T00:00:00Z", "source_context": "official-test"},
    ])


def _shelters():
    return pd.DataFrame([
        {"shelter_id": "S1", "name": "Site A", "latitude": 20.1, "longitude": 85.1, "total_capacity": 1200, "current_occupancy": 100, "water_capacity": 1000, "sanitation_capacity": 950, "access_capacity": 900, "safety_score": 90, "accessibility_score": 80, "data_mode": "LIVE", "data_timestamp": "2026-09-01T00:00:00Z", "source_context": "official-test"},
    ])


def test_operational_workspace_round_trip():
    h, ha = normalize_operational_habitations(_habitations())
    s, sa = normalize_operational_shelters(_shelters())
    assert ha["production_schema_valid"] is True
    assert sa["production_schema_valid"] is True
    payload = serialize_workspace(h, s, label="District A")
    restored_h, restored_s = restore_workspace(payload)
    assert len(restored_h) == 2
    assert len(restored_s) == 1
    assert payload["habitation_mode"] == "LIVE"


def test_dataset_mode_does_not_upgrade_unverified_data():
    assert dataset_mode(pd.DataFrame([{"x": 1}])) == "UNVERIFIED"
    assert dataset_mode(pd.DataFrame([{"data_mode": "DEMO"}])) == "DEMO"
    assert dataset_mode(pd.DataFrame([{"data_mode": "LIVE"}, {"data_mode": "CACHED"}])) == "CACHED"


def test_geographic_center_uses_uploaded_coordinates():
    lat, lon = geographic_center(_habitations())
    assert round(lat, 1) == 20.1
    assert round(lon, 1) == 85.1
