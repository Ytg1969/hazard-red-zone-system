from types import SimpleNamespace

import src.routing as routing
import src.streamlit_workspace as streamlit_workspace


def test_offline_routing_never_calls_osrm(monkeypatch):
    monkeypatch.setenv("SIH_OFFLINE_MODE", "true")

    def should_not_run(*args, **kwargs):
        raise AssertionError("OSRM must not be called in offline mode")

    monkeypatch.setattr(routing, "_osrm_route", should_not_run)
    result = routing.estimate_route((19.8135, 85.8312), (19.85, 85.88), allow_live_osrm=True)

    assert result["routing_mode"] == "haversine_fallback"
    assert result["route_status"] == "STRAIGHT_LINE_FALLBACK"
    assert "Offline field mode disables live OSRM" in result["route_note"]


def test_offline_routing_still_prefers_local_graph(monkeypatch, tmp_path):
    monkeypatch.setenv("SIH_OFFLINE_MODE", "true")
    graph = tmp_path / "roads.graphml"
    graph.write_text("placeholder", encoding="utf-8")

    expected = {
        "distance_km": 4.2,
        "travel_time_min": 8.4,
        "routing_mode": "cached_osm_graph",
        "route_geometry": [[19.8, 85.8], [19.9, 85.9]],
        "route_status": "ROAD_NETWORK_ROUTE",
        "route_note": "local",
    }
    monkeypatch.setattr(routing, "_cached_graph_route", lambda *args, **kwargs: expected)
    monkeypatch.setattr(routing, "_osrm_route", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("OSRM must not run")))

    result = routing.estimate_route((19.8, 85.8), (19.9, 85.9), graphml_path=graph, allow_live_osrm=True)
    assert result == expected


def test_offline_workspace_skips_configured_remote_feeds(monkeypatch):
    fake_st = SimpleNamespace(session_state={})
    monkeypatch.setattr(streamlit_workspace, "st", fake_st)
    monkeypatch.setattr(streamlit_workspace, "offline_mode", lambda: True)
    monkeypatch.setattr(streamlit_workspace, "operational_data_required", lambda: False)

    def should_not_run():
        raise AssertionError("configured URLs must not be resolved while offline")

    monkeypatch.setattr(streamlit_workspace, "configured_operational_urls", should_not_run)
    result = streamlit_workspace.resolve_operational_workspace(auto_configured=True, enforce_required=False)
    assert result is None


def test_offline_hazard_skips_configured_remote_source(monkeypatch):
    fake_st = SimpleNamespace(session_state={})
    monkeypatch.setattr(streamlit_workspace, "st", fake_st)
    monkeypatch.setattr(streamlit_workspace, "offline_mode", lambda: True)

    def should_not_run():
        raise AssertionError("configured hazard source must not be resolved while offline")

    monkeypatch.setattr(streamlit_workspace, "configured_hazard_source", should_not_run)
    result = streamlit_workspace.resolve_operational_hazard(auto_configured=True)
    assert result is None
