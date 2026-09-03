import pandas as pd
import pytest

from src.schema_mapping import apply_field_mapping, missing_canonical_fields, suggest_field_mapping


def test_habitation_mapping_suggests_common_government_aliases():
    df = pd.DataFrame({
        "Village Code": [101],
        "Village Name": ["Alpha"],
        "Lat": [20.1],
        "Long": [85.2],
        "TOT_POP": [1000],
        "Age 0-6": [120],
        "Age 60 Plus": [90],
    })
    mapping = suggest_field_mapping(df, "habitation")
    assert mapping == {
        "habitation_id": "Village Code",
        "name": "Village Name",
        "latitude": "Lat",
        "longitude": "Long",
        "population": "TOT_POP",
        "children_population": "Age 0-6",
        "elderly_population": "Age 60 Plus",
    }
    mapped = apply_field_mapping(df, mapping, "habitation")
    assert missing_canonical_fields(mapped, "habitation") == []


def test_shelter_mapping_rejects_duplicate_source_use():
    df = pd.DataFrame({"id": [1], "name": ["A"], "lat": [1], "lon": [2], "capacity": [50]})
    with pytest.raises(ValueError, match="multiple canonical fields"):
        apply_field_mapping(
            df,
            {"shelter_id": "id", "name": "name", "latitude": "lat", "longitude": "lon", "total_capacity": "capacity", "current_occupancy": "capacity"},
            "shelter",
        )


def test_mapping_does_not_overwrite_existing_canonical_column():
    df = pd.DataFrame({"population": [10], "pop": [11]})
    with pytest.raises(ValueError, match="already exists"):
        apply_field_mapping(df, {"population": "pop"}, "habitation")
