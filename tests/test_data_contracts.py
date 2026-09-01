import pandas as pd
import pytest

from src.data_contracts import assess_habitation_dataset, assess_shelter_dataset
from src.preprocessing import (
    HABITATION_REQUIRED,
    SHELTER_REQUIRED,
    validate_columns,
    validate_habitations,
    validate_shelters,
)


def test_habitation_contract_accepts_required_columns():
    df = pd.DataFrame(columns=sorted(HABITATION_REQUIRED))
    validate_columns(df, HABITATION_REQUIRED, "habitations")


def test_shelter_contract_accepts_required_columns():
    df = pd.DataFrame(columns=sorted(SHELTER_REQUIRED))
    validate_columns(df, SHELTER_REQUIRED, "shelters")


def test_habitation_validation_rejects_invalid_coordinates():
    df = pd.DataFrame(
        [
            {
                "habitation_id": "H1",
                "name": "Invalid",
                "latitude": 120,
                "longitude": 85,
                "population": 100,
                "children_population": 20,
                "elderly_population": 10,
            }
        ]
    )
    with pytest.raises(ValueError, match="latitude"):
        validate_habitations(df)


def test_habitation_validation_rejects_vulnerable_count_above_population():
    df = pd.DataFrame(
        [
            {
                "habitation_id": "H1",
                "name": "Invalid",
                "latitude": 20,
                "longitude": 85,
                "population": 100,
                "children_population": 80,
                "elderly_population": 30,
            }
        ]
    )
    with pytest.raises(ValueError, match="cannot exceed"):
        validate_habitations(df)


def test_shelter_validation_rejects_duplicate_ids():
    df = pd.DataFrame(
        [
            {
                "shelter_id": "S1",
                "name": "A",
                "latitude": 20,
                "longitude": 85,
                "total_capacity": 100,
                "current_occupancy": 10,
            },
            {
                "shelter_id": "S1",
                "name": "B",
                "latitude": 21,
                "longitude": 86,
                "total_capacity": 120,
                "current_occupancy": 20,
            },
        ]
    )
    with pytest.raises(ValueError, match="unique"):
        validate_shelters(df)


def test_production_habitation_assessment_accepts_valid_minimum_schema():
    df = pd.DataFrame([
        {
            "habitation_id": "H1",
            "name": "Village",
            "latitude": 20.0,
            "longitude": 85.0,
            "population": 1000,
            "children_population": 180,
            "elderly_population": 90,
        }
    ])
    result = assess_habitation_dataset(df)
    assert result["production_schema_valid"] is True
    assert result["provenance_complete"] is False


def test_production_habitation_assessment_flags_bad_population_composition():
    df = pd.DataFrame([
        {
            "habitation_id": "H1",
            "name": "Village",
            "latitude": 20.0,
            "longitude": 85.0,
            "population": 100,
            "children_population": 80,
            "elderly_population": 40,
        }
    ])
    result = assess_habitation_dataset(df)
    assert result["production_schema_valid"] is False
    assert result["population_issues"] == 1


def test_production_shelter_assessment_reports_resource_completeness():
    df = pd.DataFrame([
        {
            "shelter_id": "S1",
            "name": "Shelter",
            "latitude": 20.0,
            "longitude": 85.0,
            "total_capacity": 1000,
            "current_occupancy": 100,
            "water_capacity": 800,
            "safety_score": 90,
        }
    ])
    result = assess_shelter_dataset(df)
    assert result["production_schema_valid"] is True
    assert result["resource_completeness_pct"] == 40.0
    assert "sanitation_capacity" in result["missing_resource_fields"]


def test_production_shelter_assessment_flags_invalid_coordinates():
    df = pd.DataFrame([
        {
            "shelter_id": "S1",
            "name": "Shelter",
            "latitude": 120.0,
            "longitude": 85.0,
            "total_capacity": 1000,
            "current_occupancy": 100,
        }
    ])
    result = assess_shelter_dataset(df)
    assert result["production_schema_valid"] is False
    assert result["coordinate_issues"] == 1
