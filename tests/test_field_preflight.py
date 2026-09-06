from pathlib import Path

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
    assert any("Puri road GraphML cache is missing" in warning for warning in result["warnings"])
    assert result["launch"]["phone_url"] == "http://192.168.1.25:8501"


def test_strict_road_cache_fails_until_puri_graph_exists(monkeypatch, tmp_path: Path):
    _stub_core_checks(monkeypatch)

    missing = field_preflight.run_preflight(root=tmp_path, strict_road_cache=True)
    assert missing["core_offline_ready"] is True
    assert missing["field_ready"] is False

    puri_path = tmp_path / field_preflight.ROAD_CACHE_FILES["Puri"]
    puri_path.parent.mkdir(parents=True, exist_ok=True)
    puri_path.write_text("<graphml>cached road graph</graphml>", encoding="utf-8")

    ready = field_preflight.run_preflight(root=tmp_path, strict_road_cache=True)
    assert ready["road_routing_ready"] is True
    assert ready["field_ready"] is True


def test_road_cache_state_reports_each_demo_city(tmp_path: Path):
    chennai_path = tmp_path / field_preflight.ROAD_CACHE_FILES["Chennai"]
    chennai_path.parent.mkdir(parents=True, exist_ok=True)
    chennai_path.write_bytes(b"cached")

    state = field_preflight._road_cache_state(tmp_path)
    assert state["cities"]["Chennai"]["ready"] is True
    assert state["cities"]["Puri"]["ready"] is False
    assert state["all_demo_cities_ready"] is False
