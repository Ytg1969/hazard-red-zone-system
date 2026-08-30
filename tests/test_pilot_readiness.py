import pandas as pd

from src.pilot_readiness import habitation_readiness, pilot_readiness, shelter_readiness


def test_habitation_readiness_reports_missing_columns():
    report = habitation_readiness(pd.DataFrame([{"habitation_id": "H1", "name": "Alpha"}]))
    assert report.is_ready is False
    assert "latitude" in report.missing_columns
    assert report.ready_rows == 0


def test_habitation_readiness_counts_incomplete_rows_without_filling_values():
    df = pd.DataFrame(
        [
            {
                "habitation_id": "H1",
                "name": "Alpha",
                "latitude": 19.8,
                "longitude": 85.8,
                "population": 1000,
                "children_population": 120,
                "elderly_population": 80,
            },
            {
                "habitation_id": "H2",
                "name": "Beta",
                "latitude": None,
                "longitude": 85.9,
                "population": 800,
                "children_population": 90,
                "elderly_population": 60,
            },
        ]
    )
    report = habitation_readiness(df)
    assert report.ready_rows == 1
    assert report.readiness_percent == 50.0
    assert report.rows_missing_values["latitude"] == 1
    assert report.is_ready is False


def test_shelter_readiness_requires_real_occupancy():
    df = pd.DataFrame(
        [
            {
                "shelter_id": "S1",
                "name": "Shelter",
                "latitude": 19.9,
                "longitude": 86.0,
                "total_capacity": 1000,
                "current_occupancy": None,
            }
        ]
    )
    report = shelter_readiness(df)
    assert report.ready_rows == 0
    assert report.rows_missing_values["current_occupancy"] == 1


def test_pilot_readiness_only_true_when_both_contracts_complete():
    habitations = pd.DataFrame(
        [
            {
                "habitation_id": "H1",
                "name": "Alpha",
                "latitude": 19.8,
                "longitude": 85.8,
                "population": 1000,
                "children_population": 120,
                "elderly_population": 80,
            }
        ]
    )
    shelters = pd.DataFrame(
        [
            {
                "shelter_id": "S1",
                "name": "Shelter",
                "latitude": 19.9,
                "longitude": 86.0,
                "total_capacity": 1000,
                "current_occupancy": 0,
            }
        ]
    )
    summary = pilot_readiness(habitations, shelters)
    assert summary["operational_ready"] is True
    assert summary["habitations"]["readiness_percent"] == 100.0
    assert summary["shelters"]["readiness_percent"] == 100.0
