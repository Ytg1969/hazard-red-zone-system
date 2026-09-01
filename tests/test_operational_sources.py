from src import operational_sources
from src.live_data import DataEnvelope


HAB_CSV = """habitation_id,name,latitude,longitude,population,children_population,elderly_population,hazard_score,exposure_score,accessibility_score\nH1,Village,20,85,1000,180,90,70,65,55\n"""
SHELTER_CSV = """shelter_id,name,latitude,longitude,total_capacity,current_occupancy,water_capacity,sanitation_capacity,access_capacity,safety_score,accessibility_score\nS1,Shelter,20.1,85.1,1200,100,1000,950,900,90,80\n"""


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
    assert result["data"].iloc[0]["data_mode"] == "CACHED"
