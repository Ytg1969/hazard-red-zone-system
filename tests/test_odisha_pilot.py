import pandas as pd
import pytest

from src.odisha_pilot import (
    application_ready_habitations,
    application_ready_shelters,
    attach_coordinates,
    attach_shelter_operational_details,
    attach_vulnerability_demographics,
    stage_census_villages,
    stage_puri_shelters,
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


def _stage_census():
    return stage_census_villages(
        _raw_census(),
        column_map={
            "State": "state_name",
            "District": "district_name",
            "VillageCode": "village_code",
            "Village": "village_name",
            "Population": "population",
        },
    )


def _raw_shelters():
    return pd.DataFrame(
        [
            {
                "District": "Puri",
                "Block": "Astarang",
                "GP": "Alasahi",
                "Village": "Asana",
                "Location": "Near Somanath Temple",
                "Type": "MCS",
                "Capacity": None,
            },
            {
                "District": "Khordha",
                "Block": "Demo",
                "GP": "Demo",
                "Village": "Other",
                "Location": "School",
                "Type": "MFS",
                "Capacity": 1000,
            },
        ]
    )


def _stage_shelters():
    return stage_puri_shelters(
        _raw_shelters(),
        column_map={
            "District": "district_name",
            "Block": "block_name",
            "GP": "gp_name",
            "Village": "village_name",
            "Location": "location_name",
            "Type": "shelter_type",
            "Capacity": "total_capacity",
        },
    )


def test_stage_census_filters_puri_and_preserves_reference_year():
    staged = _stage_census()
    assert len(staged) == 1
    assert staged.iloc[0]["district_name"] == "Puri"
    assert staged.iloc[0]["population_reference_year"] == 2011
    assert staged.iloc[0]["habitation_id"] == "CEN2011-409001"
    assert staged.iloc[0]["data_mode"] == "CACHED"


def test_attach_coordinates_does_not_invent_missing_locations():
    staged = _stage_census()
    coords = pd.DataFrame(
        [{"village_code": "999999", "latitude": 19.8, "longitude": 85.8}]
    )
    merged = attach_coordinates(staged, coords)
    assert bool(merged.iloc[0]["coordinate_status"]) is False
    assert pd.isna(merged.iloc[0]["latitude"])


def test_attach_vulnerability_demographics_preserves_source_and_counts():
    staged = _stage_census()
    enriched = attach_vulnerability_demographics(
        staged,
        pd.DataFrame(
            [
                {
                    "village_code": "409001",
                    "children_population": 180,
                    "elderly_population": 90,
                }
            ]
        ),
        source_name="Authoritative demographic table",
        reference_year=2011,
    )
    assert bool(enriched.iloc[0]["demographic_status"]) is True
    assert enriched.iloc[0]["children_population"] == 180
    assert enriched.iloc[0]["elderly_population"] == 90
    assert enriched.iloc[0]["demographic_reference_year"] == 2011
    assert enriched.iloc[0]["demographic_source"] == "Authoritative demographic table"


def test_attach_vulnerability_demographics_rejects_impossible_counts():
    staged = _stage_census()
    with pytest.raises(ValueError, match="cannot exceed total population"):
        attach_vulnerability_demographics(
            staged,
            pd.DataFrame(
                [
                    {
                        "village_code": "409001",
                        "children_population": 800,
                        "elderly_population": 500,
                    }
                ]
            ),
            source_name="Authoritative demographic table",
            reference_year=2011,
        )


def test_application_ready_requires_authoritative_vulnerable_population_fields():
    staged = _stage_census()
    coords = pd.DataFrame(
        [{"village_code": "409001", "latitude": 19.81, "longitude": 85.83}]
    )
    merged = attach_coordinates(staged, coords)
    with pytest.raises(ValueError, match="authoritative enrichment"):
        application_ready_habitations(merged)


def test_application_ready_habitation_needs_both_coordinates_and_demographics():
    staged = _stage_census()
    with_coords = attach_coordinates(
        staged,
        pd.DataFrame(
            [{"village_code": "409001", "latitude": 19.81, "longitude": 85.83}]
        ),
    )
    enriched = attach_vulnerability_demographics(
        with_coords,
        pd.DataFrame(
            [
                {
                    "village_code": "409001",
                    "children_population": 180,
                    "elderly_population": 90,
                }
            ]
        ),
        source_name="Authoritative demographic table",
        reference_year=2011,
    )
    ready = application_ready_habitations(enriched)
    assert len(ready) == 1
    assert ready.iloc[0]["habitation_id"] == "CEN2011-409001"


def test_stage_puri_shelters_filters_district_and_keeps_unknown_capacity():
    staged = _stage_shelters()
    assert len(staged) == 1
    assert staged.iloc[0]["district_name"] == "Puri"
    assert staged.iloc[0]["shelter_type"] == "MCS"
    assert pd.isna(staged.iloc[0]["total_capacity"])
    assert staged.iloc[0]["data_mode"] == "CACHED"
    assert staged.iloc[0]["shelter_id"].startswith("OSDMA-PURI-")


def test_application_ready_shelters_requires_real_operational_fields():
    staged = _stage_shelters()
    with pytest.raises(ValueError, match="authoritative enrichment"):
        application_ready_shelters(staged)


def test_attach_shelter_operational_details_keeps_unknowns_unknown():
    staged = _stage_shelters()
    shelter_id = staged.iloc[0]["shelter_id"]
    enriched = attach_shelter_operational_details(
        staged,
        pd.DataFrame(
            [
                {
                    "shelter_id": shelter_id,
                    "latitude": 19.95,
                    "longitude": 86.30,
                    "total_capacity": 1000,
                    "current_occupancy": None,
                }
            ]
        ),
        source_name="Verified shelter register",
    )
    assert enriched.iloc[0]["total_capacity"] == 1000
    assert pd.isna(enriched.iloc[0]["current_occupancy"])
    assert enriched.iloc[0]["operational_source"] == "Verified shelter register"


def test_application_ready_shelters_does_not_replace_missing_occupancy_with_zero():
    staged = stage_puri_shelters(
        pd.DataFrame(
            [
                {
                    "district_name": "Puri",
                    "block_name": "Astarang",
                    "gp_name": "Alasahi",
                    "village_name": "Asana",
                    "location_name": "Public Place",
                    "shelter_type": "MCS",
                    "latitude": 19.95,
                    "longitude": 86.30,
                    "total_capacity": 1000,
                    "current_occupancy": None,
                }
            ]
        )
    )
    ready = application_ready_shelters(staged)
    assert ready.empty


def test_application_ready_shelter_requires_verified_operational_fields():
    staged = _stage_shelters()
    shelter_id = staged.iloc[0]["shelter_id"]
    enriched = attach_shelter_operational_details(
        staged,
        pd.DataFrame(
            [
                {
                    "shelter_id": shelter_id,
                    "latitude": 19.95,
                    "longitude": 86.30,
                    "total_capacity": 1000,
                    "current_occupancy": 120,
                }
            ]
        ),
        source_name="Verified shelter register",
    )
    ready = application_ready_shelters(enriched)
    assert len(ready) == 1
    assert ready.iloc[0]["current_occupancy"] == 120
