"""Transparent prototype multi-hazard scoring for DEMO / scenario use.

These indicator weights are not official hazard standards. They are explicit,
bounded prototype rules so every score can be explained and replaced later by
authoritative source-specific mappings.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class IndicatorRule:
    weight: float
    low: float
    high: float
    inverse: bool = False
    label: str = ""


HAZARD_MODELS: dict[str, dict[str, IndicatorRule]] = {
    "flood": {
        "historical_floods": IndicatorRule(0.30, 0, 10, label="Historical flood count"),
        "rainfall_intensity_mm_hr": IndicatorRule(0.25, 0, 100, label="Rainfall intensity"),
        "elevation_m": IndicatorRule(0.20, 0, 100, inverse=True, label="Low elevation"),
        "distance_to_river_km": IndicatorRule(0.15, 0, 20, inverse=True, label="River proximity"),
        "drainage_risk_score": IndicatorRule(0.10, 0, 100, label="Drainage susceptibility"),
    },
    "cyclone": {
        "wind_gust_kph": IndicatorRule(0.30, 60, 220, label="Wind-gust scenario"),
        "distance_to_coast_km": IndicatorRule(0.20, 0, 100, inverse=True, label="Coastal proximity"),
        "storm_surge_exposure_score": IndicatorRule(0.20, 0, 100, label="Storm-surge exposure"),
        "rainfall_intensity_mm_hr": IndicatorRule(0.15, 0, 100, label="Rainfall intensity"),
        "roof_vulnerability_score": IndicatorRule(0.15, 0, 100, label="Roof/building vulnerability"),
    },
    "landslide": {
        "slope_degree": IndicatorRule(0.30, 0, 45, label="Slope"),
        "rainfall_intensity_mm_hr": IndicatorRule(0.25, 0, 100, label="Rainfall intensity"),
        "soil_instability_score": IndicatorRule(0.20, 0, 100, label="Soil instability"),
        "landcover_risk_score": IndicatorRule(0.15, 0, 100, label="Land-cover susceptibility"),
        "historical_landslides": IndicatorRule(0.10, 0, 10, label="Historical landslide count"),
    },
    "earthquake": {
        "seismic_zone_score": IndicatorRule(0.30, 0, 100, label="Seismic-zone proxy"),
        "distance_to_fault_km": IndicatorRule(0.20, 0, 200, inverse=True, label="Fault proximity"),
        "building_vulnerability_score": IndicatorRule(0.20, 0, 100, label="Building vulnerability"),
        "ground_amplification_score": IndicatorRule(0.15, 0, 100, label="Ground amplification"),
        "historical_earthquakes": IndicatorRule(0.15, 0, 10, label="Historical shaking count"),
    },
    "drought": {
        "rainfall_deficit_score": IndicatorRule(0.30, 0, 100, label="Rainfall deficit"),
        "soil_moisture_deficit_score": IndicatorRule(0.20, 0, 100, label="Soil-moisture deficit"),
        "groundwater_stress_score": IndicatorRule(0.20, 0, 100, label="Groundwater stress"),
        "heat_stress_score": IndicatorRule(0.15, 0, 100, label="Heat stress"),
        "historical_droughts": IndicatorRule(0.15, 0, 10, label="Historical drought count"),
    },
}

COMBINED_MODEL_WEIGHTS = {
    "flood": 0.25,
    "cyclone": 0.20,
    "landslide": 0.20,
    "earthquake": 0.20,
    "drought": 0.15,
}

SUPPORTED_HAZARDS = tuple(HAZARD_MODELS) + ("combined",)


def _bounded_score(value: float, rule: IndicatorRule) -> float:
    if rule.high <= rule.low:
        raise ValueError("indicator scale high must exceed low")
    score = (float(value) - rule.low) / (rule.high - rule.low) * 100.0
    score = max(0.0, min(100.0, score))
    return 100.0 - score if rule.inverse else score


def _compute_single(df: pd.DataFrame, hazard_type: str) -> pd.DataFrame:
    if hazard_type not in HAZARD_MODELS:
        raise ValueError(f"unsupported hazard type: {hazard_type}")

    configured = HAZARD_MODELS[hazard_type]
    active: dict[str, IndicatorRule] = {}
    for column, rule in configured.items():
        if column in df.columns and pd.to_numeric(df[column], errors="coerce").notna().any():
            active[column] = rule

    if not active:
        raise ValueError(f"no usable {hazard_type} indicators found")

    active_total = sum(rule.weight for rule in active.values())
    components = pd.DataFrame(index=df.index)
    for column, rule in active.items():
        numeric = pd.to_numeric(df[column], errors="coerce")
        normalized = numeric.map(lambda value: _bounded_score(value, rule) if pd.notna(value) else pd.NA)
        normalized = normalized.astype("Float64")
        active_weight = rule.weight / active_total
        components[column] = normalized
        components[f"{column}_weight"] = active_weight
        components[f"{column}_contribution"] = normalized.fillna(0) * active_weight

    contribution_columns = [f"{column}_contribution" for column in active]
    components["hazard_score"] = components[contribution_columns].sum(axis=1).clip(0, 100).round(2)
    components.attrs["hazard_type"] = hazard_type
    components.attrs["active_weights"] = {
        column: round(rule.weight / active_total, 4) for column, rule in active.items()
    }
    components.attrs["data_completeness"] = round(
        sum(rule.weight for rule in active.values()) / sum(rule.weight for rule in configured.values()) * 100,
        1,
    )
    components.attrs["labels"] = {column: rule.label for column, rule in active.items()}
    return components


def compute_hazard_components(df: pd.DataFrame, hazard_type: str = "flood") -> pd.DataFrame:
    """Return transparent 0–100 prototype hazard scores and component metadata."""
    hazard_type = str(hazard_type or "flood").strip().lower().replace("all hazards", "combined")
    if hazard_type != "combined":
        return _compute_single(df, hazard_type)

    scores: dict[str, pd.Series] = {}
    completeness: dict[str, float] = {}
    for model in HAZARD_MODELS:
        try:
            result = _compute_single(df, model)
        except ValueError:
            continue
        scores[model] = result["hazard_score"]
        completeness[model] = float(result.attrs["data_completeness"])

    if not scores:
        raise ValueError("combined hazard model needs indicators for at least one hazard")

    active_total = sum(COMBINED_MODEL_WEIGHTS[model] for model in scores)
    components = pd.DataFrame(index=df.index)
    for model, score in scores.items():
        weight = COMBINED_MODEL_WEIGHTS[model] / active_total
        components[f"{model}_hazard_score"] = score
        components[f"{model}_weight"] = weight
        components[f"{model}_weighted_contribution"] = score * weight

    contribution_columns = [f"{model}_weighted_contribution" for model in scores]
    components["hazard_score"] = components[contribution_columns].sum(axis=1).clip(0, 100).round(2)
    components.attrs["hazard_type"] = "combined"
    components.attrs["active_models"] = list(scores)
    components.attrs["model_weights"] = {
        model: round(COMBINED_MODEL_WEIGHTS[model] / active_total, 4) for model in scores
    }
    components.attrs["model_completeness"] = completeness
    components.attrs["data_completeness"] = round(
        sum(completeness[model] * COMBINED_MODEL_WEIGHTS[model] for model in scores) / active_total,
        1,
    )
    return components


def compute_hazard_index(df: pd.DataFrame, hazard_type: str = "flood") -> pd.Series:
    return compute_hazard_components(df, hazard_type)["hazard_score"]
