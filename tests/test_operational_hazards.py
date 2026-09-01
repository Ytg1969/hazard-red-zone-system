import json

import pandas as pd
import pytest

from src.operational_hazards import validate_geojson_hazard
from src.pipeline import enrich_habitations


def _geojson(score=80):
    return json.dumps({
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"hazard_score": score, "hazard_type": "flood", "source": "verified-test"},
            "geometry": {"type": "Polygon", "coordinates": [[[85.0, 20.0], [86.0, 20.0], [86.0, 21.0], [85.0, 21.0], [85.0, 20.0]]]},
        }],
    })


def test_validate_operational_hazard_geojson():
    result = validate_geojson_hazard(_geojson())
    assert result["feature_count"] == 1


def test_reject_out_of_range_hazard_score():
    with pytest.raises(ValueError):
        validate_geojson_hazard(_geojson(140))


def test_stored_mode_can_use_gis_score(monkeypatch):
    habitations = pd.DataFrame([{
        "habitation_id": "H1", "name": "A", "latitude": 20.5, "longitude": 85.5,
        "population": 100, "children_population": 20, "elderly_population": 10,
        "exposure_score": 50, "accessibility_score": 50, "hazard_score": 10,
    }])

    monkeypatch.setattr("src.pipeline.calculate_hazard_exposure", lambda row, hazard_data=None: {
        "hazard_score": 80, "inside_hazard_zone": True, "distance_to_hazard_km": 0,
        "hazard_type": "flood", "hazard_source": "verified-test",
    })
    result = enrich_habitations(habitations, hazard_data=object(), hazard_type="stored", add_coordination_zones=False)
    assert float(result.iloc[0]["hazard_score"]) == 80
    assert result.iloc[0]["hazard_profile"] == "stored_gis"
