from src.routing import estimate_route


def test_route_falls_back_without_cache():
    result = estimate_route((20.27, 85.84), (20.29, 85.86))
    assert result["routing_mode"] == "haversine_fallback"
    assert result["distance_km"] > 0
    assert result["travel_time_min"] is None


def test_route_falls_back_for_missing_cache_file():
    result = estimate_route(
        (20.27, 85.84),
        (20.29, 85.86),
        graphml_path="data/cache/roads/does-not-exist.graphml",
    )
    assert result["routing_mode"] == "haversine_fallback"
