"""Readiness checks for the authoritative Odisha/Puri pilot.

These helpers make data gaps explicit before authoritative records enter the
operational risk and relocation pipeline. They report missing columns and missing
row-level values without filling them with demo or synthetic substitutes.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


HABITATION_OPERATIONAL_FIELDS = (
    "habitation_id",
    "name",
    "latitude",
    "longitude",
    "population",
    "children_population",
    "elderly_population",
)

SHELTER_OPERATIONAL_FIELDS = (
    "shelter_id",
    "name",
    "latitude",
    "longitude",
    "total_capacity",
    "current_occupancy",
)


@dataclass(frozen=True)
class ReadinessReport:
    label: str
    total_rows: int
    ready_rows: int
    missing_columns: tuple[str, ...]
    rows_missing_values: dict[str, int]

    @property
    def is_ready(self) -> bool:
        return not self.missing_columns and self.total_rows > 0 and self.ready_rows == self.total_rows

    @property
    def readiness_percent(self) -> float:
        if self.total_rows == 0:
            return 0.0
        return round(self.ready_rows / self.total_rows * 100.0, 1)

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "total_rows": self.total_rows,
            "ready_rows": self.ready_rows,
            "readiness_percent": self.readiness_percent,
            "is_ready": self.is_ready,
            "missing_columns": list(self.missing_columns),
            "rows_missing_values": dict(self.rows_missing_values),
        }


def _report(df: pd.DataFrame, required: tuple[str, ...], label: str) -> ReadinessReport:
    missing_columns = tuple(sorted(set(required) - set(df.columns)))
    if missing_columns:
        return ReadinessReport(
            label=label,
            total_rows=len(df),
            ready_rows=0,
            missing_columns=missing_columns,
            rows_missing_values={},
        )

    rows_missing_values = {field: int(df[field].isna().sum()) for field in required}
    complete_mask = df[list(required)].notna().all(axis=1)
    return ReadinessReport(
        label=label,
        total_rows=len(df),
        ready_rows=int(complete_mask.sum()),
        missing_columns=(),
        rows_missing_values=rows_missing_values,
    )


def habitation_readiness(df: pd.DataFrame) -> ReadinessReport:
    """Report whether authoritative habitation rows satisfy the frozen contract."""
    return _report(df, HABITATION_OPERATIONAL_FIELDS, "habitations")


def shelter_readiness(df: pd.DataFrame) -> ReadinessReport:
    """Report whether authoritative shelter rows satisfy the frozen contract."""
    return _report(df, SHELTER_OPERATIONAL_FIELDS, "shelters")


def pilot_readiness(habitations: pd.DataFrame, shelters: pd.DataFrame) -> dict:
    """Return a compact Phase-2 readiness summary for integration/UI use."""
    h = habitation_readiness(habitations)
    s = shelter_readiness(shelters)
    return {
        "habitations": h.as_dict(),
        "shelters": s.as_dict(),
        "operational_ready": h.is_ready and s.is_ready,
    }
