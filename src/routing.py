from __future__ import annotations

import hashlib
import os
from functools import lru_cache
from pathlib import Path

from src.live_data import fetch_json_with_cache
from src.spatial_analysis import haversine_km


OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"


def _fallback_route(origin: tuple[float, float], destination: tuple[float, float], *, note: str | None = None) -> dict:
    distance = haversine_km(origin[0], origin[1], destination[0], destination[1])
    return {
        "distance_km": round(distance, 2),
        "travel_time_min": None,
        "routing_mode": "haversine_fallback",
        "route_geometry": [
            [float(origin[0]), float(origin[1])],
            [float(destination[0]), float(destination[1])],
        ],
        "route_status": "STRAIGHT_LINE_FALLBACK",
        "route_note": note or "No road-network route was available.",
    }


def _osrm_cache_path(origin: tuple[float, float], destination: tuple[float, float]) -> Path:
    key = f"{origin[0]:.5f},{origin[1]:.5f}-{destination[0]:.5f},{destination[1]:.5f}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]
    return Path("data/cache/osrm") / f"route_{digest}.json"


def _osrm_route(origin: tuple[float, float], destination: tuple[float, float], *, timeout: float = 8.0) -> dict:
    """Fetch a real road route from the public OSRM demo service with disk-cache fallback."""
    coordinates = f"{float(origin[1])},{float(origin[0])};{float(destination[1])},{float(destination[0])}"
    url = (
        f"{OSRM_ROUTE_URL}/{coordinates}"
        "?overview=full&geometries=geojson&steps=false&alternatives=false"
    )
    envelope = fetch_json_with_cache(
        source="OSRM public routing service",
        url=url,
        cache_path=_osrm_cache_path(origin, destination),
        timeout=timeout,
    )
    payload = envelope.payload or {}
    if payload.get("code") != "Ok" or not payload.get("routes"):
        raise RuntimeError(f"OSRM route unavailable: {payload.get('code') or 'no route'}")

    route = payload["routes"][0]
    coords = (route.get("geometry") or {}).get("coordinates") or []
    geometry = [[float(lat), float(lon)] for lon, lat in coords]
    if len(geometry) < 2:
        raise RuntimeError("OSRM returned no usable route geometry")

    return {
        "distance_km": round(float(route.get("distance", 0.0)) / 1000.0, 2),
        "travel_time_min": round(float(route.get("duration", 0.0)) / 60.0, 1),
        "routing_mode": "osrm_live" if envelope.mode == "LIVE" else "osrm_cached",
        "route_geometry": geometry,
        "route_status": "ROAD_NETWORK_ROUTE",
        "route_note": "Road route from OSRM." if envelope.mode == "LIVE" else "Cached OSRM road route.",
        "source_url": envelope.source_url,
        "stale": envelope.stale,
    }


@lru_cache(maxsize=8)
def _load_graph(path_str: str):
    import osmnx as ox

    return ox.load_graphml(path_str)


def _edge_geometry(graph, u, v, data) -> list[list[float]]:
    """Return ordered [[lat, lon], ...] geometry for one OSM edge."""
    geometry = data.get("geometry")
    coords: list[list[float]] = []

    if geometry is not None and hasattr(geometry, "coords"):
        coords = [[float(lat), float(lon)] for lon, lat in geometry.coords]
    elif isinstance(geometry, str) and "LINESTRING" in geometry.upper():
        try:
            from shapely import wkt

            geom = wkt.loads(geometry)
            coords = [[float(lat), float(lon)] for lon, lat in geom.coords]
        except Exception:
            coords = []

    if not coords:
        coords = [
            [float(graph.nodes[u]["y"]), float(graph.nodes[u]["x"])],
            [float(graph.nodes[v]["y"]), float(graph.nodes[v]["x"])],
        ]

    if len(coords) >= 2:
        u_lat = float(graph.nodes[u]["y"])
        u_lon = float(graph.nodes[u]["x"])
        start_d = (coords[0][0] - u_lat) ** 2 + (coords[0][1] - u_lon) ** 2
        end_d = (coords[-1][0] - u_lat) ** 2 + (coords[-1][1] - u_lon) ** 2
        if end_d < start_d:
            coords.reverse()
    return coords


def _cached_graph_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    path: Path,
    average_speed_kmph: float,
) -> dict:
    import networkx as nx
    import osmnx as ox

    graph = _load_graph(str(path))
    origin_node = ox.distance.nearest_nodes(graph, X=float(origin[1]), Y=float(origin[0]))
    destination_node = ox.distance.nearest_nodes(graph, X=float(destination[1]), Y=float(destination[0]))
    node_path = nx.shortest_path(graph, origin_node, destination_node, weight="length")

    length_m = 0.0
    road_coords: list[list[float]] = []
    for u, v in zip(node_path[:-1], node_path[1:]):
        options = graph.get_edge_data(u, v) or {}
        if not options:
            continue
        best_key = min(options, key=lambda key: float(options[key].get("length", float("inf"))))
        data = options[best_key]
        length_m += float(data.get("length", 0.0) or 0.0)
        segment = _edge_geometry(graph, u, v, data)
        if road_coords and segment and road_coords[-1] == segment[0]:
            road_coords.extend(segment[1:])
        else:
            road_coords.extend(segment)

    if length_m <= 0 or not road_coords:
        raise RuntimeError("Cached graph did not produce a road path")

    distance_km = length_m / 1000.0
    travel_time_min = distance_km / average_speed_kmph * 60.0 if average_speed_kmph > 0 else None

    geometry = [[float(origin[0]), float(origin[1])]]
    for point in road_coords:
        if geometry[-1] != point:
            geometry.append(point)
    destination_point = [float(destination[0]), float(destination[1])]
    if geometry[-1] != destination_point:
        geometry.append(destination_point)

    return {
        "distance_km": round(distance_km, 2),
        "travel_time_min": round(travel_time_min, 1) if travel_time_min is not None else None,
        "routing_mode": "cached_osm_graph",
        "graphml_path": str(path),
        "route_geometry": geometry,
        "route_status": "ROAD_NETWORK_ROUTE",
        "route_note": "Road route from the locally cached OpenStreetMap graph.",
    }


def estimate_route(
    origin: tuple[float, float],
    destination: tuple[float, float],
    graphml_path: str | Path | None = None,
    average_speed_kmph: float = 30.0,
    *,
    allow_live_osrm: bool = False,
) -> dict:
    """Estimate a route with a safe fallback chain.

    Order of preference:
    1. locally cached OpenStreetMap GraphML road network;
    2. OSRM road route when `allow_live_osrm=True`, with disk-cache reuse;
    3. explicit straight-line haversine fallback.

    No traffic/congestion claim is made. Routing never bypasses shelter safety or
    capacity selection; this function only computes the path to the already
    selected shelter.
    """
    configured_path = graphml_path or os.getenv("SIH_ROAD_GRAPHML")
    graph_error = None
    if configured_path:
        path = Path(configured_path)
        if path.exists():
            try:
                return _cached_graph_route(origin, destination, path, average_speed_kmph)
            except Exception as exc:
                graph_error = str(exc)

    if allow_live_osrm:
        try:
            return _osrm_route(origin, destination)
        except Exception as exc:
            note = f"Road routing unavailable; using straight-line fallback. OSRM: {exc}"
            if graph_error:
                note += f" Cached graph: {graph_error}"
            return _fallback_route(origin, destination, note=note)

    note = "No cached road graph available."
    if graph_error:
        note = f"Cached graph route failed: {graph_error}"
    return _fallback_route(origin, destination, note=note)
