from src.carrying_capacity import calculate_capacity
from src.routing import estimate_route


DEFAULT_RELOCATION_WEIGHTS = {
    "safety": 0.35,
    "capacity": 0.25,
    "accessibility": 0.20,
    "distance": 0.20,
}


def relocation_priority(risk_level: str, vulnerability_score: float) -> str:
    vulnerability_score = float(vulnerability_score)
    risk_level = str(risk_level).upper()
    if risk_level == "CRITICAL" and vulnerability_score >= 60:
        return "IMMEDIATE"
    if risk_level in {"CRITICAL", "HIGH"}:
        return "SHORT_TERM"
    if risk_level == "MODERATE":
        return "MEDIUM_TERM"
    return "MONITOR"


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def _distance_score(distance_km: float, reference_km: float = 30.0) -> float:
    """Convert route distance into a 0–100 desirability score.

    0 km -> 100. Distances at or beyond reference_km -> 0.
    This is a transparent prototype normalization, not a universal standard.
    """
    if reference_km <= 0:
        raise ValueError("reference_km must be positive")
    return max(0.0, 100.0 * (1.0 - float(distance_km) / reference_km))


def rank_shelters(
    habitation: dict,
    shelters: list[dict],
    weights: dict | None = None,
    minimum_safety_score: float = 50.0,
) -> list[dict]:
    weights = weights or DEFAULT_RELOCATION_WEIGHTS
    required = {"safety", "capacity", "accessibility", "distance"}
    if set(weights) != required or abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("relocation weights must contain safety/capacity/accessibility/distance and sum to 1.0")

    population = max(0.0, float(habitation.get("population", 0) or 0))
    origin = (float(habitation["latitude"]), float(habitation["longitude"]))
    candidates: list[dict] = []

    for shelter in shelters:
        safety_score = _bounded(shelter.get("safety_score", 0))
        if safety_score < minimum_safety_score:
            continue

        capacity = calculate_capacity(shelter)
        available = capacity["available_capacity"]
        if available <= 0:
            continue

        destination = (float(shelter["latitude"]), float(shelter["longitude"]))
        route = estimate_route(origin, destination)
        distance_km = float(route["distance_km"])

        capacity_score = 100.0 if population <= 0 else min(100.0, available / population * 100.0)
        accessibility_score = _bounded(shelter.get("accessibility_score", 50))
        distance_score = _distance_score(distance_km)

        suitability = (
            weights["safety"] * safety_score
            + weights["capacity"] * capacity_score
            + weights["accessibility"] * accessibility_score
            + weights["distance"] * distance_score
        )

        candidates.append(
            {
                "shelter_id": shelter.get("shelter_id"),
                "shelter_name": shelter.get("name"),
                "latitude": float(shelter["latitude"]),
                "longitude": float(shelter["longitude"]),
                "distance_km": round(distance_km, 2),
                "travel_time_min": route.get("travel_time_min"),
                "routing_mode": route.get("routing_mode", "unknown"),
                "safety_score": round(safety_score, 2),
                "accessibility_score": round(accessibility_score, 2),
                "effective_capacity": capacity["effective_capacity"],
                "available_capacity": available,
                "capacity_validation_status": capacity["capacity_validation_status"],
                "capacity_adequacy_score": round(capacity_score, 2),
                "distance_score": round(distance_score, 2),
                "suitability_score": round(suitability, 2),
            }
        )

    return sorted(candidates, key=lambda item: item["suitability_score"], reverse=True)


def recommend_shelter(habitation: dict, shelters: list[dict]) -> dict | None:
    ranked = rank_shelters(habitation, shelters)
    return ranked[0] if ranked else None


def allocate_population(
    habitation: dict,
    shelters: list[dict],
) -> dict:
    """Allocate a habitation population across ranked shelters without overfilling."""
    remaining = max(0, int(float(habitation.get("population", 0) or 0)))
    allocations: list[dict] = []

    for candidate in rank_shelters(habitation, shelters):
        if remaining <= 0:
            break
        capacity = int(candidate["available_capacity"])
        assigned = min(remaining, capacity)
        if assigned <= 0:
            continue
        allocations.append(
            {
                "shelter_id": candidate["shelter_id"],
                "shelter_name": candidate["shelter_name"],
                "assigned_population": assigned,
                "distance_km": candidate["distance_km"],
                "suitability_score": candidate["suitability_score"],
            }
        )
        remaining -= assigned

    return {
        "required_population": int(float(habitation.get("population", 0) or 0)),
        "allocated_population": int(float(habitation.get("population", 0) or 0)) - remaining,
        "remaining_deficit": remaining,
        "allocations": allocations,
    }
