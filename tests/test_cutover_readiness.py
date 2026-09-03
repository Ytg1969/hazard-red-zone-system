import pandas as pd

from src.cutover_readiness import assess_cutover_readiness


def _habitations(mode="LIVE"):
    return pd.DataFrame([
        {
            "habitation_id": "H1",
            "name": "Village A",
            "latitude": 20.0,
            "longitude": 85.0,
            "population": 1000,
            "children_population": 180,
            "elderly_population": 90,
            "data_mode": mode,
            "data_timestamp": "2026-09-01T00:00:00Z",
            "source_context": "Authority habitation source",
        }
    ])


def _shelters(mode="LIVE", include_resources=True):
    row = {
        "shelter_id": "S1",
        "name": "Relocation Site A",
        "latitude": 20.05,
        "longitude": 85.05,
        "total_capacity": 1200,
        "current_occupancy": 100,
        "data_mode": mode,
        "data_timestamp": "2026-09-01T00:00:00Z",
        "source_context": "Authority relocation-site source",
    }
    if include_resources:
        row.update({
            "water_capacity": 1100,
            "sanitation_capacity": 1050,
            "access_capacity": 1000,
            "safety_score": 90,
            "accessibility_score": 85,
        })
    return pd.DataFrame([row])


def test_cutover_ready_only_when_all_gates_pass():
    result = assess_cutover_readiness(_habitations(), _shelters(), hazard_ready=True)
    assert result["ready_for_demo_removal"] is True
    assert result["readiness_pct"] == 100.0


def test_demo_mode_blocks_cutover():
    result = assess_cutover_readiness(_habitations("DEMO"), _shelters(), hazard_ready=True)
    assert result["ready_for_demo_removal"] is False
    check = next(item for item in result["checks"] if item["key"] == "operational_modes")
    assert check["pass"] is False


def test_missing_capacity_evidence_blocks_cutover():
    result = assess_cutover_readiness(_habitations(), _shelters(include_resources=False), hazard_ready=True)
    assert result["ready_for_demo_removal"] is False
    check = next(item for item in result["checks"] if item["key"] == "capacity_evidence")
    assert check["pass"] is False


def test_uncalibrated_hazard_blocks_cutover():
    result = assess_cutover_readiness(_habitations(), _shelters(), hazard_ready=False)
    assert result["ready_for_demo_removal"] is False
    check = next(item for item in result["checks"] if item["key"] == "calibrated_hazard")
    assert check["pass"] is False
