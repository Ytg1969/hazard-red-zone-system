import pandas as pd
import pytest

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
