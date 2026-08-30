import pandas as pd
import pytest

from src.odisha_pilot import (
    application_ready_habitations,
    attach_coordinates,
    stage_census_villages,
)


def _raw_census():
    return pd.DataFrame(
        [
            {
                "State": "Odisha",
                "District": "Puri",
                "VillageCode": "409001",
                "Village": "Alpha",
                "Population": 1200,
            },
            {
                "State": "Odisha",
                "District": "Khordha",
                "VillageCode": "410001",
                "Village": "Beta",
                "Population": 900,
            },
        ]
    )


def test_stage_census_filters_puri_and_preserves_reference_year():
    staged = stage_census_villages(
        _raw_census(),
        column_map={
            "State": "state_name",
            "District": "district_name",
            "VillageCode": "village_code",
            "Village": "village_name",
            "Population": "population",
        },
    )
    assert len(staged) == 1
    assert staged.iloc[0]["district_name"] == "Puri"
    assert staged.iloc[0]["population_reference_year"] == 2011
    assert staged.iloc[0]["habitation_id"] == "CEN2011-409001"
    assert staged.iloc[0]["data_mode"] == "CACHED"


def test_attach_coordinates_does_not_invent_missing_locations():
    staged = stage_census_villages(
        _raw_census(),
        column_map={
            "State": "state_name",
            "District": "district_name",
            "VillageCode": "village_code",
            "Village": "village_name",
            "Population": "population",
        },
    )
    coords = pd.DataFrame(
        [{"village_code": "999999", "latitude": 19.8, "longitude": 85.8}]
    )
    merged = attach_coordinates(staged, coords)
    assert bool(merged.iloc[0]["coordinate_status"]) is False
    assert pd.isna(merged.iloc[0]["latitude"])


def test_application_ready_requires_authoritative_vulnerable_population_fields():
    staged = stage_census_villages(
        _raw_census(),
        column_map={
            "State": "state_name",
            "District": "district_name",
            "VillageCode": "village_code",
            "Village": "village_name",
            "Population": "population",
        },
    )
    coords = pd.DataFrame(
        [{"village_code": "409001", "latitude": 19.81, "longitude": 85.83}]
    )
    merged = attach_coordinates(staged, coords)
    with pytest.raises(ValueError, match="authoritative enrichment"):
        application_ready_habitations(merged)
