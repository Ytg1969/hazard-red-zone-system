"""Authoritative-data staging helpers for the Odisha pilot.

This module intentionally separates demographic ingestion from coordinate enrichment.
Census 2011 population values are preserved with their source year and are never
presented as current population. Records only become application-ready habitations
after a coordinate join succeeds.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


CENSUS_SOURCE_NAME = "Census of India 2011 - Primary Census Abstract / Basic Population Figures"
CENSUS_SOURCE_YEAR = 2011
PILOT_STATE = "Odisha"
PILOT_DISTRICT = "Puri"


STAGING_REQUIRED = {
    "state_name",
    "district_name",
    "village_code",
    "village_name",
    "population",
}


def stage_census_villages(
    df: pd.DataFrame,
    *,
    district: str = PILOT_DISTRICT,
    column_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Normalize Census village population records for the Odisha pilot.

    ``column_map`` maps source-column names to the canonical staging names in
    ``STAGING_REQUIRED``. The function does not invent coordinates or vulnerable
    population counts that the supplied source does not contain.
    """
    data = df.copy()
    if column_map:
        data = data.rename(columns=column_map)

    missing = sorted(STAGING_REQUIRED - set(data.columns))
    if missing:
        raise ValueError(f"census staging data is missing required columns: {missing}")

    data["state_name"] = data["state_name"].astype(str).str.strip()
    data["district_name"] = data["district_name"].astype(str).str.strip()
    data["village_name"] = data["village_name"].astype(str).str.strip()
    data["village_code"] = data["village_code"].astype(str).str.strip()
    data["population"] = pd.to_numeric(data["population"], errors="raise")

    if (data["population"] < 0).any():
        raise ValueError("census population cannot be negative")

    subset = data[
        data["state_name"].str.casefold().eq(PILOT_STATE.casefold())
        & data["district_name"].str.casefold().eq(str(district).strip().casefold())
    ].copy()

    subset = subset[subset["village_code"].ne("") & subset["village_name"].ne("")]
    if subset["village_code"].duplicated().any():
        raise ValueError("census village_code values must be unique within the pilot subset")

    subset["habitation_id"] = "CEN2011-" + subset["village_code"]
    subset["name"] = subset["village_name"]
    subset["data_mode"] = "CACHED"
    subset["population_reference_year"] = CENSUS_SOURCE_YEAR
    subset["population_source"] = CENSUS_SOURCE_NAME

    keep = [
        "habitation_id",
        "name",
        "state_name",
        "district_name",
        "village_code",
        "population",
        "population_reference_year",
        "population_source",
        "data_mode",
    ]
    return subset[keep].reset_index(drop=True)


def attach_coordinates(
    staged: pd.DataFrame,
    coordinates: pd.DataFrame,
) -> pd.DataFrame:
    """Join verified WGS84 village coordinates to Census staging records.

    Coordinates must be keyed by ``village_code`` and include latitude/longitude.
    Rows without coordinates remain excluded from application-ready output rather
    than receiving synthetic coordinates.
    """
    required = {"village_code", "latitude", "longitude"}
    missing = sorted(required - set(coordinates.columns))
    if missing:
        raise ValueError(f"coordinate data is missing required columns: {missing}")

    coords = coordinates.copy()
    coords["village_code"] = coords["village_code"].astype(str).str.strip()
    if coords["village_code"].duplicated().any():
        raise ValueError("coordinate village_code values must be unique")

    coords["latitude"] = pd.to_numeric(coords["latitude"], errors="raise")
    coords["longitude"] = pd.to_numeric(coords["longitude"], errors="raise")
    if not coords["latitude"].between(-90, 90).all():
        raise ValueError("latitude must be between -90 and 90")
    if not coords["longitude"].between(-180, 180).all():
        raise ValueError("longitude must be between -180 and 180")

    merged = staged.merge(
        coords[["village_code", "latitude", "longitude"]],
        on="village_code",
        how="left",
        validate="one_to_one",
    )
    merged["coordinate_status"] = merged["latitude"].notna() & merged["longitude"].notna()
    return merged


def application_ready_habitations(
    staged_with_coordinates: pd.DataFrame,
) -> pd.DataFrame:
    """Return records that can safely enter the current habitation pipeline.

    The current core contract requires children and elderly population. Census
    basic-population staging does not guarantee those fields, so callers must
    enrich them from an authoritative demographic table before using this helper.
    """
    required = {
        "habitation_id",
        "name",
        "latitude",
        "longitude",
        "population",
        "children_population",
        "elderly_population",
    }
    missing = sorted(required - set(staged_with_coordinates.columns))
    if missing:
        raise ValueError(
            "pilot data is not application-ready; authoritative enrichment is still required for: "
            + ", ".join(missing)
        )

    ready = staged_with_coordinates.dropna(subset=["latitude", "longitude"]).copy()
    return ready


def load_census_excel(
    path: str | Path,
    *,
    sheet_name=0,
    district: str = PILOT_DISTRICT,
    column_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Read a locally downloaded Census workbook and stage the pilot subset."""
    raw = pd.read_excel(Path(path), sheet_name=sheet_name)
    return stage_census_villages(raw, district=district, column_map=column_map)
