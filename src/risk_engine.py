DEFAULT_WEIGHTS = {
    "hazard": 0.35,
    "exposure": 0.25,
    "vulnerability": 0.25,
    "accessibility": 0.15,
}

REQUIRED_WEIGHT_KEYS = {"hazard", "exposure", "vulnerability", "accessibility"}


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def validate_weights(weights: dict) -> dict:
    if set(weights) != REQUIRED_WEIGHT_KEYS:
        raise ValueError(f"weights must contain exactly {sorted(REQUIRED_WEIGHT_KEYS)}")
    normalized = {key: float(value) for key, value in weights.items()}
    if any(value < 0 for value in normalized.values()):
        raise ValueError("risk weights cannot be negative")
    if abs(sum(normalized.values()) - 1.0) > 1e-6:
        raise ValueError("risk weights must sum to 1.0")
    return normalized


def classify_risk(score: float) -> str:
    score = _bounded(score)
    if score >= 70:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 30:
        return "MODERATE"
    return "LOW"


def calculate_risk(habitation: dict, weights: dict | None = None) -> dict:
    weights = validate_weights(weights or DEFAULT_WEIGHTS)

    values = {
        "hazard": _bounded(habitation.get("hazard_score", 0)),
        "exposure": _bounded(habitation.get("exposure_score", 0)),
        "vulnerability": _bounded(habitation.get("vulnerability_score", 0)),
        "accessibility": _bounded(habitation.get("accessibility_score", 0)),
    }
    contributions = {key: weights[key] * values[key] for key in REQUIRED_WEIGHT_KEYS}
    score = sum(contributions.values())
    level = classify_risk(score)
    drivers = sorted(contributions.items(), key=lambda item: item[1], reverse=True)

    return {
        "risk_score": round(score, 2),
        "risk_level": level,
        "drivers": [name for name, _ in drivers[:2]],
        "components": values,
        "weights": weights,
        "contributions": {key: round(value, 2) for key, value in contributions.items()},
    }
