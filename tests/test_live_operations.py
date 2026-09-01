import src.live_operations as live_operations


def test_distance_filter_keeps_only_nearby_events():
    rows = [
        {"name": "near", "latitude": 19.82, "longitude": 85.84},
        {"name": "far", "latitude": 28.61, "longitude": 77.21},
        {"name": "bad", "latitude": None, "longitude": None},
    ]
    result = live_operations._distance_filter(rows, 19.8135, 85.8312, 100)
    assert [row["name"] for row in result] == ["near"]
    assert result[0]["distance_km"] >= 0


def test_safe_call_degrades_to_demo():
    def boom():
        raise RuntimeError("offline")

    result = live_operations._safe_call("Example", boom)
    assert result["mode"] == "DEMO"
    assert result["source"] == "Example"
    assert "offline" in result["error"]


def test_operations_snapshot_preserves_context_only_contract(monkeypatch):
    monkeypatch.setattr(
        live_operations,
        "fetch_weather_at_location",
        lambda *args, **kwargs: {"source": "weather", "mode": "LIVE", "stale": False, "current": {"temperature_2m": 30}},
    )
    monkeypatch.setattr(
        live_operations,
        "fetch_air_quality_at_location",
        lambda *args, **kwargs: {"source": "air", "mode": "LIVE", "stale": False, "current": {"us_aqi": 50}},
    )
    monkeypatch.setattr(
        live_operations,
        "fetch_recent_earthquakes_at_location",
        lambda *args, **kwargs: {"source": "usgs", "mode": "LIVE", "stale": False, "events": []},
    )
    monkeypatch.setattr(
        live_operations,
        "fetch_gdacs_events",
        lambda *args, **kwargs: {"source": "gdacs", "mode": "LIVE", "stale": False, "events": []},
    )
    monkeypatch.setattr(
        live_operations,
        "fetch_eonet_events",
        lambda *args, **kwargs: {"source": "eonet", "mode": "LIVE", "stale": False, "events": []},
    )
    monkeypatch.setattr(
        live_operations,
        "fetch_imd_context",
        lambda *args, **kwargs: {"source": "imd", "mode": "DEMO", "stale": False, "warnings": [], "rainfall": []},
    )
    monkeypatch.setattr(
        live_operations,
        "fetch_disaster_alerts",
        lambda *args, **kwargs: {"source": "sachet", "mode": "DEMO", "stale": False, "alerts": []},
    )

    result = live_operations.fetch_operations_snapshot("Puri", days=7, radius_km=500, min_magnitude=2.5)
    assert result["city"] == "Puri"
    assert result["analytical_effect"] == "CONTEXT_ONLY"
    assert len(result["source_health"]) == 7
    assert result["sources"]["weather"]["mode"] == "LIVE"
