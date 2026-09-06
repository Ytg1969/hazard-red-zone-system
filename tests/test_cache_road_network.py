from pathlib import Path

import pytest

import scripts.cache_road_network as cache_road_network


def test_configure_osmnx_bounds_timeout(monkeypatch):
    monkeypatch.setattr(cache_road_network.ox.settings, "requests_timeout", 180)
    monkeypatch.setattr(cache_road_network.ox.settings, "use_cache", False)

    cache_road_network._configure_osmnx(5)

    assert cache_road_network.ox.settings.requests_timeout == 30
    assert cache_road_network.ox.settings.use_cache is True


def test_retry_succeeds_after_transient_failure(monkeypatch):
    calls = []
    sleeps = []

    def operation():
        calls.append(len(calls) + 1)
        if len(calls) == 1:
            raise RuntimeError("temporary upstream failure")
        return "ok"

    monkeypatch.setattr(cache_road_network.time, "sleep", lambda seconds: sleeps.append(seconds))

    result = cache_road_network._retry(
        operation,
        label="Puri, Odisha, India",
        attempts=2,
        retry_delay=3,
    )

    assert result == "ok"
    assert calls == [1, 2]
    assert sleeps == [3.0]


def test_retry_fails_closed_after_attempt_budget(monkeypatch):
    monkeypatch.setattr(cache_road_network.time, "sleep", lambda seconds: None)

    with pytest.raises(RuntimeError, match="after 2 attempt"):
        cache_road_network._retry(
            lambda: (_ for _ in ()).throw(RuntimeError("overpass unavailable")),
            label="Puri",
            attempts=2,
            retry_delay=0,
        )


def test_cache_network_retries_and_writes_only_verified_graph(monkeypatch, tmp_path: Path):
    attempts = []
    saved = []
    graph = object()

    def graph_from_place(place, *, network_type, simplify):
        attempts.append(place)
        if len(attempts) == 1:
            raise RuntimeError("transient")
        return graph

    monkeypatch.setattr(cache_road_network.ox, "graph_from_place", graph_from_place)
    monkeypatch.setattr(
        cache_road_network.ox,
        "save_graphml",
        lambda value, *, filepath: saved.append((value, Path(filepath))),
    )
    monkeypatch.setattr(cache_road_network.time, "sleep", lambda seconds: None)

    path = cache_road_network.cache_network(
        "Puri, Odisha, India",
        tmp_path,
        attempts=2,
        request_timeout=45,
        retry_delay=0,
    )

    assert attempts == ["Puri, Odisha, India", "Puri, Odisha, India"]
    assert path == tmp_path / "Puri_Odisha_India.graphml"
    assert saved == [(graph, path)]
    assert cache_road_network.ox.settings.requests_timeout == 45


def test_demo_cities_propagate_retry_contract(monkeypatch, tmp_path: Path):
    seen = []

    def fake_cache(place, output_dir, **kwargs):
        seen.append((place, Path(output_dir), kwargs))
        return Path(output_dir) / f"{cache_road_network.safe_filename(place)}.graphml"

    monkeypatch.setattr(cache_road_network, "cache_network", fake_cache)

    paths = cache_road_network.cache_demo_cities(
        tmp_path,
        attempts=3,
        request_timeout=90,
        retry_delay=4,
    )

    assert len(paths) == 3
    assert [item[0] for item in seen] == list(cache_road_network.DEMO_CITY_PLACES.values())
    for _, output_dir, kwargs in seen:
        assert output_dir == tmp_path
        assert kwargs == {"attempts": 3, "request_timeout": 90, "retry_delay": 4}
