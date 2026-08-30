import pandas as pd
import pytest

from src.pilot_builder import prepare_pilot_tables, write_processed_pilot


def _ready_habitations():
    return pd.DataFrame(
        [
            {
                "habitation_id": "CEN2011-1",
                "name": "Village A",
                "latitude": 19.8,
                "longitude": 85.8,
                "population": 1000,
                "children_population": 120,
                "elderly_population": 80,
                "data_mode": "CACHED",
            }
        ]
    )


def _ready_shelters():
    return pd.DataFrame(
        [
            {
                "shelter_id": "OSDMA-PURI-1",
                "name": "Shelter A",
                "latitude": 19.82,
                "longitude": 85.84,
                "total_capacity": 500,
                "current_occupancy": 100,
                "data_mode": "CACHED",
            }
        ]
    )


def test_prepare_pilot_tables_validates_when_fully_ready():
    habitations, shelters, report = prepare_pilot_tables(
        _ready_habitations(), _ready_shelters()
    )
    assert report["operational_ready"] is True
    assert len(habitations) == 1
    assert len(shelters) == 1


def test_prepare_pilot_tables_returns_partial_report_without_filling_values():
    shelters = _ready_shelters()
    shelters.loc[0, "current_occupancy"] = None
    _, returned_shelters, report = prepare_pilot_tables(
        _ready_habitations(), shelters
    )
    assert report["operational_ready"] is False
    assert pd.isna(returned_shelters.loc[0, "current_occupancy"])


def test_write_processed_pilot_refuses_partial_data(tmp_path):
    habitations = _ready_habitations()
    habitations.loc[0, "elderly_population"] = None
    with pytest.raises(ValueError, match="not operational-ready"):
        write_processed_pilot(
            habitations,
            _ready_shelters(),
            output_dir=tmp_path,
        )
    assert not (tmp_path / "habitations.csv").exists()
    assert not (tmp_path / "shelters.csv").exists()


def test_write_processed_pilot_writes_ready_tables(tmp_path):
    result = write_processed_pilot(
        _ready_habitations(),
        _ready_shelters(),
        output_dir=tmp_path,
    )
    assert result["readiness"]["operational_ready"] is True
    assert (tmp_path / "habitations.csv").exists()
    assert (tmp_path / "shelters.csv").exists()
