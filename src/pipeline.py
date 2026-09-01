"""Shared end-to-end orchestration for the SIH26191 application."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.carrying_capacity import calculate_capacity
from src.coordination_zones import assign_coordination_zones
from src.hazard_model import SUPPORTED_HAZARDS, compute_hazard_components
from src.preprocessing import (
    load_habitations,
    load_shelters,
    validate_habitations,
    validate_shelters,
)
from src.relocation import recommend_shelter, relocation_priority
from src.risk_engine import DEFAULT_WEIGHTS, calculate_risk
from src.spatial_analysis import calculate_hazard_exposure, load_hazard_layer
from src.vulnerability import calculate_vulnerability


DEMO_HABITATIONS = Path("data/demo/habitations.csv")
DEMO_SHELTERS = Path("data/demo/shelters.csv")
DEMO_HAZARDS = Path("data/demo/hazards.geojson")
MULTICITY_HABITATIONS = Path("data/demo/multicity_habitations.csv")
MULTICITY_SHELTERS = Path("data/demo/multicity_shelters.csv")
MULTICITY_HAZARDS = Path("data/demo/multicity_hazards.geojson")
DEMO_CITIES = ("Puri", "Guwahati", "Chennai")


def load_demo_data(
    city: str | None = None,
    *,
    multicity: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load the presentation dataset; optional city filtering keeps relocation local."""
    habitation_path = MULTICITY_HABITATIONS if multicity else DEMO_HABITATIONS
    shelter_path = MULTICITY_SHELTERS if multicity else DEMO_SHELTERS
    habitations = load_habitations(habitation_path)
    shelters = load_shelters(shelter_path)
    if city and city != "All Demo Cities":
        if "demo_city" in habitations.columns:
            habitations = habitations[habitations["demo_city"] == city].copy()
        if "demo_city" in shelters.columns:
            shelters = shelters[shelters["demo_city"] == city].copy()
    return habitations, shelters


def load_uploaded_habitations(uploaded_file) -> pd.DataFrame:
    """Validate a user-supplied habitation CSV without inventing missing values."""
    if uploaded_file is None:
        raise ValueError("no habitation upload supplied")
    uploaded_file.seek(0)
    return validate_habitations(pd.read_csv(uploaded_file))


def load_uploaded_shelters(uploaded_file) -> pd.DataFrame:
    """Validate a user-supplied shelter CSV without inventing missing values."""
    if uploaded_file is None:
        raise ValueError("no shelter upload supplied")
    uploaded_file.seek(0)
    return validate_shelters(pd.read_csv(uploaded_file))


@lru_cache(maxsize=2)
def _load_demo_hazards_cached(multicity: bool, path_str: str, mtime_ns: int):
    # mtime_ns participates in the cache key so local data updates invalidate
    # the cached GeoDataFrame automatically.
    del multicity, mtime_ns
    return load_hazard_layer(path_str)


def load_demo_hazards(*, multicity: bool = True):
    path = MULTICITY_HAZARDS if multicity else DEMO_HAZARDS
    resolved = path.resolve()
    cached = _load_demo_hazards_cached(multicity, str(resolved), resolved.stat().st_mtime_ns)
    return cached.copy(deep=True)


def enrich_habitations(
    habitations: pd.DataFrame,
    weights: dict | None = None,
    hazard_data=None,
    hazard_type: str = "combined",
    *,
    add_coordination_zones: bool = True,
) -> pd.DataFrame:
    """Run GIS exposure → transparent hazard profile → vulnerability → frozen risk model.

    The hazard profile only supplies the 0–100 hazard component. The frozen
    explainable risk contract and its thresholds/weights remain unchanged.
    """
    weights = weights or DEFAULT_WEIGHTS
    work = habitations.copy()

    if hazard_data is not None:
        spatial_rows: list[dict] = []
        for row in work.to_dict(orient="records"):
            spatial = calculate_hazard_exposure(row, hazard_data=hazard_data)
            row["gis_hazard_score"] = spatial.get("hazard_score")
            row["inside_hazard_zone"] = spatial.get("inside_hazard_zone")
            row["distance_to_hazard_km"] = spatial.get("distance_to_hazard_km")
            row["gis_hazard_type"] = spatial.get("hazard_type")
            spatial_rows.append(row)
        work = pd.DataFrame(spatial_rows)

    normalized_hazard_type = str(hazard_type or "combined").lower()
    if normalized_hazard_type not in SUPPORTED_HAZARDS and normalized_hazard_type != "stored":
        raise ValueError(f"unsupported hazard profile: {hazard_type}")

    if normalized_hazard_type != "stored":
        try:
            components = compute_hazard_components(work, normalized_hazard_type)
            work["hazard_score"] = components["hazard_score"].astype(float).values
            work["hazard_profile"] = normalized_hazard_type
            work["hazard_data_completeness"] = float(components.attrs.get("data_completeness", 0.0))
            active = components.attrs.get("active_models", [normalized_hazard_type])
            work["active_hazard_models"] = ", ".join(active)
        except ValueError:
            work["hazard_profile"] = "stored"
            work["hazard_data_completeness"] = 0.0
            work["active_hazard_models"] = "Stored hazard score fallback"
    else:
        work["hazard_profile"] = "stored"
        work["hazard_data_completeness"] = 100.0
        work["active_hazard_models"] = "Stored hazard score"

    records: list[dict] = []
    for row in work.to_dict(orient="records"):
        vulnerability = calculate_vulnerability(row)
        row.update(vulnerability)
        risk = calculate_risk(row, weights=weights)
        row.update(
            {
                "risk_score": risk["risk_score"],
                "risk_level": risk["risk_level"],
                "risk_drivers": ", ".join(risk["drivers"]),
                "risk_contributions": risk["contributions"],
                "relocation_priority": relocation_priority(
                    risk["risk_level"], row["vulnerability_score"]
                ),
            }
        )
        records.append(row)

    result = pd.DataFrame(records)
    if add_coordination_zones and not result.empty:
        result = assign_coordination_zones(result, n_clusters=min(3, len(result)))
    return result


def enrich_shelters(shelters: pd.DataFrame) -> pd.DataFrame:
    records: list[dict] = []
    for row in shelters.to_dict(orient="records"):
        capacity = calculate_capacity(row)
        row.update(
            {
                "effective_capacity": capacity["effective_capacity"],
                "available_capacity": capacity["available_capacity"],
                "capacity_validation_status": capacity["capacity_validation_status"],
            }
        )
        records.append(row)
    return pd.DataFrame(records)


def calculate_summary(habitations: pd.DataFrame, shelters: pd.DataFrame) -> dict:
    critical = habitations[habitations["risk_level"] == "CRITICAL"]
    high_or_critical = habitations[habitations["risk_level"].isin(["HIGH", "CRITICAL"])]
    return {
        "habitations_monitored": int(len(habitations)),
        "critical_red_zones": int(len(critical)),
        "population_at_risk": int(high_or_critical["population"].sum()),
        "immediate_relocation_population": int(
            habitations.loc[
                habitations["relocation_priority"] == "IMMEDIATE", "population"
            ].sum()
        ),
        "available_shelter_capacity": float(shelters["available_capacity"].sum()),
    }


def get_habitation(habitations: pd.DataFrame, habitation_id: str) -> dict:
    match = habitations[habitations["habitation_id"].astype(str) == str(habitation_id)]
    if match.empty:
        raise KeyError(f"Unknown habitation_id: {habitation_id}")
    return match.iloc[0].to_dict()


def relocation_for_habitation(habitation: dict, shelters: pd.DataFrame) -> dict | None:
    local_shelters = shelters
    city = habitation.get("demo_city")
    if city and "demo_city" in shelters.columns:
        local_shelters = shelters[shelters["demo_city"] == city]
    return recommend_shelter(habitation, local_shelters.to_dict(orient="records"))
