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
