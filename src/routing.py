from src.spatial_analysis import haversine_km


def estimate_route(origin: tuple[float, float], destination: tuple[float, float]) -> dict:
    """Offline-safe routing contract.

    Member 4 can replace this with cached OSMnx/NetworkX routing. This fallback
    intentionally returns straight-line distance and labels the routing mode.
    """
    distance = haversine_km(origin[0], origin[1], destination[0], destination[1])
    return {
        "distance_km": round(distance, 2),
        "travel_time_min": None,
        "routing_mode": "haversine_fallback",
    }
