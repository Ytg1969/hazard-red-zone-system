from math import radians, sin, cos, sqrt, atan2


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dlambda / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def calculate_hazard_exposure(habitation: dict, hazard_data=None) -> dict:
    """Stable interface for Member 2.

    Replace the fallback logic with real vector/raster intersection. Until then,
    an existing hazard_score on the habitation is passed through safely.
    """
    score = max(0.0, min(100.0, float(habitation.get("hazard_score", 0))))
    return {"hazard_score": score, "source": "provided_or_demo"}
