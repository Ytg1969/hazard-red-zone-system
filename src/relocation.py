from src.carrying_capacity import calculate_capacity
from src.spatial_analysis import haversine_km


def relocation_priority(risk_level: str, vulnerability_score: float) -> str:
    vulnerability_score = float(vulnerability_score)
    if risk_level == "CRITICAL" and vulnerability_score >= 60:
        return "IMMEDIATE"
    if risk_level in {"CRITICAL", "HIGH"}:
        return "SHORT_TERM"
    if risk_level == "MODERATE":
        return "MEDIUM_TERM"
    return "MONITOR"


def recommend_shelter(habitation: dict, shelters: list[dict]) -> dict | None:
    candidates = []
    for shelter in shelters:
        if float(shelter.get("safety_score", 0)) < 50:
            continue
        capacity = calculate_capacity(shelter)
        if capacity["available_capacity"] <= 0:
            continue
        distance = haversine_km(
            float(habitation["latitude"]), float(habitation["longitude"]),
            float(shelter["latitude"]), float(shelter["longitude"]),
        )
        candidates.append((distance, shelter, capacity))

    if not candidates:
        return None

    distance, shelter, capacity = min(candidates, key=lambda x: x[0])
    return {
        "shelter_id": shelter.get("shelter_id"),
        "shelter_name": shelter.get("name"),
        "distance_km": round(distance, 2),
        "available_capacity": capacity["available_capacity"],
        "routing_mode": "haversine_fallback",
    }
