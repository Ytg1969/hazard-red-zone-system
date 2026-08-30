"""Shared end-to-end orchestration for the SIH26191 demo application.

This module intentionally contains no Streamlit code. UI pages call these
functions so the analytical pipeline remains testable and reusable.
"""

from pathlib import Path

import pandas as pd

from src.carrying_capacity import calculate_capacity
from src.preprocessing import load_habitations, load_shelters
from src.relocation import recommend_shelter, relocation_priority
from src.risk_engine import DEFAULT_WEIGHTS, calculate_risk
from src.vulnerability import calculate_vulnerability


DEMO_HABITATIONS = Path("data/demo/habitations.csv")
DEMO_SHELTERS = Path("data/demo/shelters.csv")


def load_demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_habitations(DEMO_HABITATIONS), load_shelters(DEMO_SHELTERS)


def enrich_habitations(
    habitations: pd.DataFrame,
    weights: dict | None = None,
) -> pd.DataFrame:
    weights = weights or DEFAULT_WEIGHTS
    records: list[dict] = []

    for row in habitations.to_dict(orient="records"):
        vulnerability = calculate_vulnerability(row)
        row.update(vulnerability)
        risk = calculate_risk(row, weights=weights)
        row.update(
            {
                "risk_score": risk["risk_score"],
                "risk_level": risk["risk_level"],
                "risk_drivers": ", ".join(risk["drivers"]),
                "relocation_priority": relocation_priority(
                    risk["risk_level"], row["vulnerability_score"]
                ),
            }
        )
        records.append(row)

    return pd.DataFrame(records)


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


def relocation_for_habitation(
    habitation: dict,
    shelters: pd.DataFrame,
) -> dict | None:
    return recommend_shelter(habitation, shelters.to_dict(orient="records"))
