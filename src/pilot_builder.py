"""Build and validate processed Puri pilot tables from already-enriched inputs.

This module is intentionally orchestration-only: it never invents missing values.
Callers must supply authoritative/enriched habitation and shelter tables that satisfy
existing readiness gates before outputs are written for operational use.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.pilot_readiness import pilot_readiness
from src.preprocessing import validate_habitations, validate_shelters


def prepare_pilot_tables(
    habitations: pd.DataFrame,
    shelters: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Validate authoritative pilot tables and return a readiness summary.

    The function refuses to validate partial rows as operational-ready. Missing
    values stay missing and are surfaced through the readiness report.
    """
    report = pilot_readiness(habitations, shelters)
    if not report["operational_ready"]:
        return habitations.copy(), shelters.copy(), report

    validated_habitations = validate_habitations(habitations.copy())
    validated_shelters = validate_shelters(shelters.copy())
    return validated_habitations, validated_shelters, report


def write_processed_pilot(
    habitations: pd.DataFrame,
    shelters: pd.DataFrame,
    *,
    output_dir: str | Path = "data/pilot/processed",
) -> dict:
    """Write processed pilot CSVs only when every required row is operational-ready."""
    ready_h, ready_s, report = prepare_pilot_tables(habitations, shelters)
    if not report["operational_ready"]:
        raise ValueError("pilot data is not operational-ready; refusing to write processed files")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    habitation_path = out / "habitations.csv"
    shelter_path = out / "shelters.csv"
    ready_h.to_csv(habitation_path, index=False)
    ready_s.to_csv(shelter_path, index=False)

    return {
        "habitations_path": str(habitation_path),
        "shelters_path": str(shelter_path),
        "readiness": report,
    }
