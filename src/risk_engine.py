DEFAULT_WEIGHTS = {
    "hazard": 0.35,
    "exposure": 0.25,
    "vulnerability": 0.25,
    "accessibility": 0.15,
}


def _bounded(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


def classify_risk(score: float) -> str:
    if score >= 70:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 30:
        return "MODERATE"
    return "LOW"


def calculate_risk(habitation: dict, weights: dict | None = None) -> dict:
    weights = weights or DEFAULT_WEIGHTS
    required = {"hazard", "exposure", "vulnerability", "accessibility"}
    if set(weights) != required:
        raise ValueError(f"weights must contain exactly {sorted(required)}")
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("risk weights must sum to 1.0")

    values = {
        "hazard": _bounded(habitation.get("hazard_score", 0)),
        "exposure": _bounded(habitation.get("exposure_score", 0)),
        "vulnerability": _bounded(habitation.get("vulnerability_score", 0)),
        "accessibility": _bounded(habitation.get("accessibility_score", 0)),
    }
    score = sum(weights[k] * values[k] for k in required)
    level = classify_risk(score)
    drivers = sorted(values.items(), key=lambda x: x[1], reverse=True)
    return {
        "risk_score": round(score, 2),
        "risk_level": level,
        "drivers": [name for name, _ in drivers[:2]],
        "components": values,
    }
