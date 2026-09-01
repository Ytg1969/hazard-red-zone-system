"""Helpers for operator-supplied production datasets and workspace handoff."""
from __future__ import annotations

from typing import Any

import pandas as pd

from src.data_contracts import assess_habitation_dataset, assess_shelter_dataset
from src.preprocessing import validate_habitations, validate_shelters


WORKSPACE_VERSION = 1


def normalize_operational_habitations(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    work = validate_habitations(df.copy())
    assessment = assess_habitation_dataset(work)
    if not assessment["production_schema_valid"]:
        raise ValueError(f"habitation dataset failed production checks: {assessment}")
    return work, assessment


def normalize_operational_shelters(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    work = validate_shelters(df.copy())
    assessment = assess_shelter_dataset(work)
    if not assessment["production_schema_valid"]:
        raise ValueError(f"shelter dataset failed production checks: {assessment}")
    return work, assessment


def dataset_mode(df: pd.DataFrame) -> str:
    if "data_mode" not in df.columns or df.empty:
        return "UNVERIFIED"
    modes = {str(value).upper().strip() for value in df["data_mode"].dropna().tolist()}
    if modes == {"LIVE"}:
        return "LIVE"
    if modes and modes.issubset({"LIVE", "CACHED"}):
        return "CACHED"
    if "DEMO" in modes:
        return "DEMO"
    return "UNVERIFIED"


def geographic_center(df: pd.DataFrame) -> tuple[float, float]:
    if df.empty:
        raise ValueError("dataset is empty")
    lat = pd.to_numeric(df["latitude"], errors="coerce")
    lon = pd.to_numeric(df["longitude"], errors="coerce")
    if lat.isna().all() or lon.isna().all():
        raise ValueError("dataset has no valid coordinates")
    return float(lat.mean()), float(lon.mean())


def serialize_workspace(habitations: pd.DataFrame, shelters: pd.DataFrame, *, label: str) -> dict[str, Any]:
    lat, lon = geographic_center(habitations)
    return {
        "version": WORKSPACE_VERSION,
        "label": str(label or "Operational dataset").strip(),
        "habitations": habitations.to_dict(orient="records"),
        "shelters": shelters.to_dict(orient="records"),
        "habitation_mode": dataset_mode(habitations),
        "shelter_mode": dataset_mode(shelters),
        "center": {"latitude": lat, "longitude": lon},
    }


def restore_workspace(payload: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame]:
    if int(payload.get("version", 0)) != WORKSPACE_VERSION:
        raise ValueError("unsupported workspace version")
    habitations = pd.DataFrame(payload.get("habitations", []))
    shelters = pd.DataFrame(payload.get("shelters", []))
    return validate_habitations(habitations), validate_shelters(shelters)
