import sys
from types import SimpleNamespace

import networkx as nx

import src.routing as routing


def _tiny_drive_graph():
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = "EPSG:4326"
    graph.add_node(1, y=19.8000, x=85.8200)
    graph.add_node(2, y=19.8050, x=85.8250)
    graph.add_node(3, y=19.8100, x=85.8300)
    graph.add_edge(1, 2, key=0, length=800.0)
    graph.add_edge(2, 3, key=0, length=900.0)
    return graph


def test_cached_graph_route_does_not_require_osmnx_nearest_nodes(monkeypatch, tmp_path):
    graph = _tiny_drive_graph()
    graph_path = tmp_path / "roads.graphml"
    graph_path.write_text("placeholder", encoding="utf-8")

    def forbidden_nearest_nodes(*args, **kwargs):
        raise AssertionError("cached routing must not require OSMnx BallTree/scikit-learn nearest_nodes")

    fake_ox = SimpleNamespace(
        load_graphml=lambda path: graph,
        distance=SimpleNamespace(nearest_nodes=forbidden_nearest_nodes),
    )
    monkeypatch.setitem(sys.modules, "osmnx", fake_ox)
    routing._load_graph.cache_clear()
    routing._graph_node_index.cache_clear()

    result = routing._cached_graph_route(
        (19.7999, 85.8199),
        (19.8101, 85.8301),
        graph_path,
        30.0,
    )

    assert result["routing_mode"] == "cached_osm_graph"
    assert result["route_status"] == "ROAD_NETWORK_ROUTE"
    assert result["distance_km"] == 1.7
    assert len(result["route_geometry"]) >= 3


def test_nearest_graph_node_uses_lat_lon_coordinates_without_optional_spatial_index(monkeypatch, tmp_path):
    graph = _tiny_drive_graph()
    graph_path = tmp_path / "roads.graphml"
    graph_path.write_text("placeholder", encoding="utf-8")

    monkeypatch.setattr(routing, "_load_graph", lambda path: graph)
    routing._graph_node_index.cache_clear()

    assert routing._nearest_graph_node(str(graph_path), (19.8001, 85.8201)) == 1
    assert routing._nearest_graph_node(str(graph_path), (19.8099, 85.8299)) == 3
