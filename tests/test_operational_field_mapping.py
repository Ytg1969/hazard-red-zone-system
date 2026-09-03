import pytest

from src.operational_sources import configured_field_mapping


def test_configured_habitation_field_mapping_from_json(monkeypatch):
    monkeypatch.setenv("SIH_HABITATION_FIELD_MAP", '{"habitation_id":"Village Code","population":"TOT_POP"}')
    assert configured_field_mapping("habitation") == {
        "habitation_id": "Village Code",
        "population": "TOT_POP",
    }


def test_invalid_configured_field_mapping_is_rejected(monkeypatch):
    monkeypatch.setenv("SIH_SHELTER_FIELD_MAP", "not-json")
    with pytest.raises(ValueError, match="valid JSON"):
        configured_field_mapping("shelter")
