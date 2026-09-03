from src import operational_sources
from src.live_data import DataEnvelope


RAW_CSV = "Village Code,Village Name,Lat,Lon,Persons\n123,Example Village,20.1,85.2,1500\n"
RAW_GEOJSON = """{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [85.2, 20.1]},
      "properties": {"Village Code": "123", "Village Name": "Example Village", "Persons": 1500}
    }
  ]
}"""


def test_preview_preserves_raw_csv_columns(monkeypatch, tmp_path):
    monkeypatch.setattr(
        operational_sources,
        "fetch_text_with_cache",
        lambda **kwargs: DataEnvelope(
            source="test",
            mode="LIVE",
            fetched_at="2026-09-03T00:00:00+00:00",
            payload=RAW_CSV,
            source_url=kwargs["url"],
        ),
    )
    result = operational_sources.fetch_operational_preview(
        "https://example.test/authority.csv",
        cache_path=tmp_path / "preview.json",
    )
    assert result["mode"] == "LIVE"
    assert result["format"] == "csv"
    assert list(result["data"].columns) == ["Village Code", "Village Name", "Lat", "Lon", "Persons"]
    assert "data_mode" not in result["data"].columns


def test_preview_geojson_extracts_point_coordinates_without_schema_validation(monkeypatch, tmp_path):
    monkeypatch.setattr(
        operational_sources,
        "fetch_text_with_cache",
        lambda **kwargs: DataEnvelope(
            source="test",
            mode="CACHED",
            fetched_at="2026-09-03T00:00:00+00:00",
            payload=RAW_GEOJSON,
            stale=True,
            source_url=kwargs["url"],
        ),
    )
    result = operational_sources.fetch_operational_preview(
        "https://example.test/authority.geojson",
        cache_path=tmp_path / "preview.json",
    )
    assert result["format"] == "geojson"
    assert result["stale"] is True
    row = result["data"].iloc[0]
    assert float(row["latitude"]) == 20.1
    assert float(row["longitude"]) == 85.2
    assert row["Village Code"] == "123"
