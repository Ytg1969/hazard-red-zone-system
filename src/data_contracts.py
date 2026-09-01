"""Authoritative-ingestion contracts for habitation, shelter and hazard datasets.

These helpers are deliberately stricter than the minimum demo CSV validators.
They are intended for production-readiness checks and operator feedback without
silently inventing missing operational values.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

HABITATION_PRODUCTION_REQUIRED = {
    "habitation_id",
    "name",
    "latitude",
    "longitude",
    "population",
    "children_population",
    "elderly_population",
}

SHELTER_PRODUCTION_REQUIRED = {
    "shelter_id",
    "name",
    "latitude",
    "longitude",
    "total_capacity",
    "current_occupancy",
}

PROVENANCE_RECOMMENDED = {
    "data_mode",
    "data_timestamp",
    "source_context",
}

SHELTER_RESOURCE_FIELDS = {
    "water_capacity",
    "sanitation_capacity",
    "access_capacity",
    "safety_score",
    "accessibility_score",
}


def _missing(df: pd.DataFrame, required: set[str]) -> list[str]:
    return sorted(required - set(df.columns))


def _null_counts(df: pd.DataFrame, fields: set[str]) -> dict[str, int]:
    return {field: int(df[field].isna().sum()) for field in sorted(fields & set(df.columns))}


def assess_habitation_dataset(df: pd.DataFrame) -> dict[str, Any]:
    missing_required = _missing(df, HABITATION_PRODUCTION_REQUIRED)
    missing_provenance = _missing(df, PROVENANCE_RECOMMENDED)
    duplicated_ids = 0
    if "habitation_id" in df.columns:
        duplicated_ids = int(df["habitation_id"].astype(str).duplicated().sum())

    coordinate_issues = 0
    if {"latitude", "longitude"}.issubset(df.columns):
        lat = pd.to_numeric(df["latitude"], errors="coerce")
        lon = pd.to_numeric(df["longitude"], errors="coerce")
        coordinate_issues = int((lat.isna() | lon.isna() | ~lat.between(-90, 90) | ~lon.between(-180, 180)).sum())

    population_issues = 0
    if {"population", "children_population", "elderly_population"}.issubset(df.columns):
        pop = pd.to_numeric(df["population"], errors="coerce")
        child = pd.to_numeric(df["children_population"], errors="coerce")
        elderly = pd.to_numeric(df["elderly_population"], errors="coerce")
        population_issues = int((pop.isna() | child.isna() | elderly.isna() | (pop < 0) | (child < 0) | (elderly < 0) | ((child + elderly) > pop)).sum())

    production_ready = not missing_required and duplicated_ids == 0 and coordinate_issues == 0 and population_issues == 0
    return {
        "dataset_type": "habitations",
        "rows": int(len(df)),
        "production_schema_valid": production_ready,
        "missing_required": missing_required,
        "missing_provenance": missing_provenance,
        "duplicate_ids": duplicated_ids,
        "coordinate_issues": coordinate_issues,
        "population_issues": population_issues,
        "null_counts": _null_counts(df, HABITATION_PRODUCTION_REQUIRED),
        "provenance_complete": not missing_provenance,
    }


def assess_shelter_dataset(df: pd.DataFrame) -> dict[str, Any]:
    missing_required = _missing(df, SHELTER_PRODUCTION_REQUIRED)
    missing_provenance = _missing(df, PROVENANCE_RECOMMENDED)
    missing_resources = _missing(df, SHELTER_RESOURCE_FIELDS)
    duplicated_ids = 0
    if "shelter_id" in df.columns:
        duplicated_ids = int(df["shelter_id"].astype(str).duplicated().sum())

    coordinate_issues = 0
    if {"latitude", "longitude"}.issubset(df.columns):
        lat = pd.to_numeric(df["latitude"], errors="coerce")
        lon = pd.to_numeric(df["longitude"], errors="coerce")
        coordinate_issues = int((lat.isna() | lon.isna() | ~lat.between(-90, 90) | ~lon.between(-180, 180)).sum())

    capacity_issues = 0
    if {"total_capacity", "current_occupancy"}.issubset(df.columns):
        total = pd.to_numeric(df["total_capacity"], errors="coerce")
        occupied = pd.to_numeric(df["current_occupancy"], errors="coerce")
        capacity_issues = int((total.isna() | occupied.isna() | (total < 0) | (occupied < 0)).sum())

    production_ready = not missing_required and duplicated_ids == 0 and coordinate_issues == 0 and capacity_issues == 0
    resource_completeness = round(100.0 * (len(SHELTER_RESOURCE_FIELDS) - len(missing_resources)) / len(SHELTER_RESOURCE_FIELDS), 1)
    return {
        "dataset_type": "shelters",
        "rows": int(len(df)),
        "production_schema_valid": production_ready,
        "missing_required": missing_required,
        "missing_provenance": missing_provenance,
        "missing_resource_fields": missing_resources,
        "resource_completeness_pct": resource_completeness,
        "duplicate_ids": duplicated_ids,
        "coordinate_issues": coordinate_issues,
        "capacity_issues": capacity_issues,
        "null_counts": _null_counts(df, SHELTER_PRODUCTION_REQUIRED | SHELTER_RESOURCE_FIELDS),
        "provenance_complete": not missing_provenance,
    }
