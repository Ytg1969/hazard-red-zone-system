from src import operational_sources
from src.live_data import DataEnvelope


HAB_CSV = """habitation_id,name,latitude,longitude,population,children_population,elderly_population,hazard_score,exposure_score,accessibility_score\nH1,Village,20,85,1000,180,90,70,65,55\n"""
SHELTER_CSV = """shelter_id,name,latitude,longitude,total_capacity,current_occupancy,water_capacity,sanitation_capacity,access_capacity,safety_score,accessibility_score\nS1,Shelter,20.1,85.1,1200,100,1000,950,900,90,80\n"""
HAB_GEOJSON = """{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [85.0, 20.0]},
      "properties": {
        "habitation_id": "H1",
        "name": "Village",
        "population": 1000,
        "children_population": 180,
        "elderly_population": 90,
        "hazard_score": 70,
        "exposure_score": 65,
        "accessibility_score": 55
      }
    }
  ]
}"""
SHELTER_GEOJSON = """{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [85.1, 20.1]},
      "properties": {
        "shelter_id": "S1",
        "name": "Shelter",
        "total_capacity": 1200,
        "current_occupancy": 100,
        "water_capacity": 1000,
        "sanitation_capacity": 950,
        "access_capacity": 900,
        "safety_score": 90,
        "accessibility_score": 80
      }
    }
  ]
}"""


def test_operational_feed_requires_https():
    try:
        operational_sources.fetch_operational_habitations("http://example.test/h.csv")
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("HTTP operational URL should be rejected")


def test_habitation_feed_sets_live_provenance(monkeypatch, tmp_path):
    monkeypatch.setattr(
        operational_sources,
        "fetch_text_with_cache",
        lambda **kwargs: DataEnvelope(source="test", mode="LIVE", fetched_at="2026-09-01T00:00:00+00:00", payload=HAB_CSV, source_url=kwargs["url"]),
    )
    result = operational_sources.fetch_operational_habitations("https://example.test/h.csv", cache_path=tmp_path / "h.json")
    assert result["mode"] == "LIVE"
    assert result["format"] == "csv"
    assert result["data"].iloc[0]["data_mode"] == "LIVE"
    assert result["data"].iloc[0]["source_context"] == "https://example.test/h.csv"


def test_shelter_feed_preserves_cached_mode(monkeypatch, tmp_path):
    monkeypatch.setattr(
        operational_sources,
        "fetch_text_with_cache",
        lambda **kwargs: DataEnvelope(source="test", mode="CACHED", fetched_at="2026-09-01T00:00:00+00:00", payload=SHELTER_CSV, stale=True, source_url=kwargs["url"]),
    )
    result = operational_sources.fetch_operational_shelters("https://example.test/s.csv", cache_path=tmp_path / "s.json")
    assert result["mode"] == "CACHED"
    assert result["stale"] is True
    assert result["format"] == "csv"
    assert result["data"].iloc[0]["data_mode"] == "CACHED"


def test_configured_habitation_geojson_uses_point_geometry(monkeypatch, tmp_path):
    monkeypatch.setattr(
        operational_sources,
        "fetch_text_with_cache",
        lambda **kwargs: DataEnvelope(source="test", mode="LIVE", fetched_at="2026-09-01T00:00:00+00:00", payload=HAB_GEOJSON, source_url=kwargs["url"]),
    )
    result = operational_sources.fetch_operational_habitations("https://example.test/h.geojson", cache_path=tmp_path / "h.json")
    assert result["format"] == "geojson"
    row = result["data"].iloc[0]
    assert float(row["latitude"]) == 20.0
    assert float(row["longitude"]) == 85.0
    assert row["source_context"] == "https://example.test/h.geojson"


def test_configured_shelter_geojson_uses_point_geometry(monkeypatch, tmp_path):
    monkeypatch.setattr(
        operational_sources,
        "fetch_text_with_cache",
        lambda **kwargs: DataEnvelope(source="test", mode="LIVE", fetched_at="2026-09-01T00:00:00+00:00", payload=SHELTER_GEOJSON, source_url=kwargs["url"]),
    )
    result = operational_sources.fetch_operational_shelters("https://example.test/s.geojson", cache_path=tmp_path / "s.json")
    assert result["format"] == "geojson"
    row = result["data"].iloc[0]
    assert float(row["latitude"]) == 20.1
    assert float(row["longitude"]) == 85.1
    assert int(row["total_capacity"]) == 1200
