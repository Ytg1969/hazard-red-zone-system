from src.eonet_context import CATEGORY_MAP
from src.location_context import search_locations


def test_eonet_category_registry_covers_demo_calamities():
    assert CATEGORY_MAP["Flood"] == "floods"
    assert CATEGORY_MAP["Cyclone / Severe Storm"] == "severeStorms"
    assert CATEGORY_MAP["Landslide"] == "landslides"
    assert CATEGORY_MAP["Wildfire"] == "wildfires"
    assert CATEGORY_MAP["All calamities"] is None


def test_location_search_rejects_too_short_query_without_network():
    result = search_locations("x")
    assert result["mode"] == "DEMO"
    assert result["results"] == []
    assert "two characters" in result["error"]


def test_location_search_uses_bundled_index_offline(monkeypatch):
    monkeypatch.setenv("SIH_OFFLINE_MODE", "true")
    result = search_locations("Puri")
    assert result["access_status"] == "OFFLINE"
    assert result["source"] == "Bundled offline location index"
    assert result["results"][0]["name"] == "Puri"


def test_location_search_returns_empty_for_unknown_offline_location(monkeypatch):
    monkeypatch.setenv("SIH_OFFLINE_MODE", "true")
    result = search_locations("Vijayawada")
    assert result["access_status"] == "OFFLINE"
    assert result["results"] == []
