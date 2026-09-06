from pathlib import Path

import pandas as pd

import scripts.field_preflight as field_preflight


def _stub_core_checks(monkeypatch):
    monkeypatch.setattr(
        field_preflight,
        "_dependency_state",
        lambda: {"pass": True, "missing": [], "required": []},
    )
    monkeypatch.setattr(
        field_preflight,
        "_required_files_state",
        lambda root: {"pass": True, "missing": [], "required": []},
    )
    monkeypatch.setattr(
        field_preflight,
        "_port_state",
        lambda port: {"pass": True, "port": port, "error": None},
    )
    monkeypatch.setattr(
        field_preflight,
        "_git_state",
        lambda root: {"available": True, "commit": "abc1234", "clean": True, "changed_entries": 0},
    )
    monkeypatch.setattr(field_preflight, "_lan_ip", lambda: "192.168.1.25")
    monkeypatch.setattr(
        field_preflight,
        "_run_offline_gates",
        lambda: ({"demo_ready": True}, {"production_ready_offline": True}),
    )


def test_missing_road_cache_is_warning_by_default(monkeypatch, tmp_path: Path):
    _stub_core_checks(monkeypatch)
    result = field_preflight.run_preflight(root=tmp_path, strict_road_cache=False)

    assert result["core_offline_ready"] is True
    assert result["field_ready"] is True
    assert result["road_routing_ready"] is False
    assert result["checks"]["puri_route_validation"]["attempted"] is False
    assert any("Puri road GraphML cache is missing" in warning for warning in result["warnings"])
    assert result["launch"]["phone_url"] == "http://192.168.1.25:8501"


def test_strict_road_cache_rejects_present_but_invalid_graph(monkeypatch, tmp_path: Path):
    _stub_core_checks(monkeypatch)
    puri_path = tmp_path / field_preflight.ROAD_CACHE_FILES["Puri"]
    puri_path.parent.mkdir(parents=True, exist_ok=True)
    puri_path.write_text("<graphml>not a usable graph</graphml>", encoding="utf-8")

    result = field_preflight.run_preflight(root=tmp_path, strict_road_cache=True)

    assert result["core_offline_ready"] is True
    assert result["checks"]["road_cache"]["puri_ready"] is True
    assert result["checks"]["puri_route_validation"]["attempted"] is True
    assert result["road_routing_ready"] is False
    assert result["field_ready"] is False
    assert any("failed cached-route validation" in warning for warning in result["warnings"])


def test_strict_road_cache_passes_only_after_route_validation(monkeypatch, tmp_path: Path):
    _stub_core_checks(monkeypatch)
    puri_path = tmp_path / field_preflight.ROAD_CACHE_FILES["Puri"]
    puri_path.parent.mkdir(parents=True, exist_ok=True)
    puri_path.write_bytes(b"real-graph-placeholder")

    monkeypatch.setattr(
        field_preflight,
        "_validate_puri_road_route",
        lambda root, road_state: {
            "attempted": True,
            "pass": True,
            "routing_mode": "cached_osm_graph",
            "route_status": "ROAD_NETWORK_ROUTE",
            "distance_km": 4.2,
            "travel_time_min": 8.4,
            "habitation": "Puri Coastal Cluster A",
            "shelter": "Puri Demo Cyclone Shelter A",
            "graph_path": field_preflight.ROAD_CACHE_FILES["Puri"],
            "error": None,
        },
    )

    result = field_preflight.run_preflight(root=tmp_path, strict_road_cache=True)

    assert result["road_routing_ready"] is True
    assert result["field_ready"] is True
    assert result["checks"]["puri_route_validation"]["routing_mode"] == "cached_osm_graph"


def test_validate_puri_route_requires_cached_graph_mode(monkeypatch, tmp_path: Path):
    puri_path = tmp_path / field_preflight.ROAD_CACHE_FILES["Puri"]
    puri_path.parent.mkdir(parents=True, exist_ok=True)
    puri_path.write_bytes(b"graph")
    road_state = field_preflight._road_cache_state(tmp_path)

    habitation = {
        "name": "Puri Coastal Cluster A",
        "latitude": 19.7983,
        "longitude": 85.8249,
        "risk_score": 80.0,
        "demo_city": "Puri",
    }
    shelter_frame = pd.DataFrame([{"demo_city": "Puri"}])
    shelter = {
        "shelter_name": "Puri Demo Cyclone Shelter A",
        "latitude": 19.815,
        "longitude": 85.835,
    }

    monkeypatch.setattr(
        field_preflight,
        "load_demo_data",
        lambda city: (pd.DataFrame([habitation]), shelter_frame),
    )
    monkeypatch.setattr(field_preflight, "load_demo_hazards", lambda: object())
    monkeypatch.setattr(field_preflight, "enrich_habitations", lambda *args, **kwargs: pd.DataFrame([habitation]))
    monkeypatch.setattr(field_preflight, "enrich_shelters", lambda *args, **kwargs: shelter_frame)
    monkeypatch.setattr(field_preflight, "rank_shelters", lambda *args, **kwargs: [shelter])
    monkeypatch.setattr(
        field_preflight,
        "estimate_route",
        lambda *args, **kwargs: {
            "distance_km": 3.0,
            "travel_time_min": None,
            "routing_mode": "haversine_fallback",
            "route_status": "STRAIGHT_LINE_FALLBACK",
            "route_geometry": [[19.7983, 85.8249], [19.815, 85.835]],
        },
    )

    result = field_preflight._validate_puri_road_route(tmp_path, road_state)
    assert result["attempted"] is True
    assert result["pass"] is False
    assert "cached graph did not produce" in result["error"]


def test_road_cache_state_reports_each_demo_city(tmp_path: Path):
    chennai_path = tmp_path / field_preflight.ROAD_CACHE_FILES["Chennai"]
    chennai_path.parent.mkdir(parents=True, exist_ok=True)
    chennai_path.write_bytes(b"cached")

    state = field_preflight._road_cache_state(tmp_path)
    assert state["cities"]["Chennai"]["ready"] is True
    assert state["cities"]["Puri"]["ready"] is False
    assert state["all_demo_cities_ready"] is False
