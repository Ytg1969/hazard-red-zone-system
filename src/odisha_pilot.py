"""Authoritative-data staging helpers for the Odisha pilot.

This module intentionally separates demographic/shelter ingestion from coordinate
and operational enrichment. Historical Census values keep their source year.
Shelter capacities/occupancy remain unknown unless the supplied authority source
actually provides them. Nothing is silently invented to satisfy the core schema.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


CENSUS_SOURCE_NAME = "Census of India 2011 - Primary Census Abstract / Basic Population Figures"
CENSUS_SOURCE_YEAR = 2011
OSDMA_SHELTER_SOURCE_NAME = "OSDMA / Puri District Disaster Management Plan shelter inventory"
OSDMA_SHELTER_SOURCE_URL = "https://www.osdma.org/plan-and-policy/district-disaster-management-plan/"
PILOT_STATE = "Odisha"
PILOT_DISTRICT = "Puri"


STAGING_REQUIRED = {
    "state_name",
    "district_name",
    "village_code",
    "village_name",
    "population",
}

SHELTER_STAGING_REQUIRED = {
    "district_name",
    "block_name",
    "gp_name",
    "village_name",
    "location_name",
    "shelter_type",
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


def _slug(value: object) -> str:
    text = str(value or "").strip().casefold()
    return "-".join(part for part in "".join(ch if ch.isalnum() else " " for ch in text).split())


def stage_puri_shelters(
    df: pd.DataFrame,
    *,
    column_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Stage the authoritative Puri MCS/MFS inventory without inventing capacity.

    The Puri DDMP/OSDMA inventory reliably supplies administrative location and
    shelter type. Some rows/tables may also supply capacity, coordinates or other
    fields; those are preserved when present. Missing capacity/occupancy stays
    missing rather than being converted to zero.
    """
    data = df.copy()
    if column_map:
        data = data.rename(columns=column_map)

    missing = sorted(SHELTER_STAGING_REQUIRED - set(data.columns))
    if missing:
        raise ValueError(f"shelter staging data is missing required columns: {missing}")

    for column in SHELTER_STAGING_REQUIRED:
        data[column] = data[column].fillna("").astype(str).str.strip()

    data = data[
        data["district_name"].str.casefold().eq(PILOT_DISTRICT.casefold())
        & data["village_name"].ne("")
    ].copy()

    allowed_types = {"MCS", "MFS"}
    data["shelter_type"] = data["shelter_type"].str.upper()
    invalid_types = sorted(set(data.loc[~data["shelter_type"].isin(allowed_types), "shelter_type"]))
    if invalid_types:
        raise ValueError(f"unsupported shelter types: {invalid_types}")

    base_id = (
        data["block_name"].map(_slug)
        + "-"
        + data["gp_name"].map(_slug)
        + "-"
        + data["village_name"].map(_slug)
    )
    if base_id.duplicated().any():
        counts = base_id.groupby(base_id).cumcount().astype(str)
        base_id = base_id + "-" + counts

    data["shelter_id"] = "OSDMA-PURI-" + base_id.str.upper()
    data["name"] = data["village_name"] + " " + data["shelter_type"]
    data["shelter_source"] = OSDMA_SHELTER_SOURCE_NAME
    data["shelter_source_url"] = OSDMA_SHELTER_SOURCE_URL
    data["data_mode"] = "CACHED"

    optional_numeric = [
        "latitude",
        "longitude",
        "total_capacity",
        "current_occupancy",
        "water_capacity",
        "sanitation_capacity",
        "access_capacity",
        "safety_score",
        "accessibility_score",
    ]
    for column in optional_numeric:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    if "latitude" in data.columns:
        invalid = data["latitude"].dropna()
        if not invalid.between(-90, 90).all():
            raise ValueError("shelter latitude must be between -90 and 90")
    if "longitude" in data.columns:
        invalid = data["longitude"].dropna()
        if not invalid.between(-180, 180).all():
            raise ValueError("shelter longitude must be between -180 and 180")

    for column in ["total_capacity", "current_occupancy", "water_capacity", "sanitation_capacity", "access_capacity"]:
        if column in data.columns and (data[column].dropna() < 0).any():
            raise ValueError(f"{column} cannot be negative")

    keep = [
        "shelter_id",
        "name",
        "district_name",
        "block_name",
        "gp_name",
        "village_name",
        "location_name",
        "shelter_type",
        "shelter_source",
        "shelter_source_url",
        "data_mode",
    ]
    keep.extend(column for column in optional_numeric if column in data.columns)
    return data[keep].reset_index(drop=True)


def application_ready_shelters(staged: pd.DataFrame) -> pd.DataFrame:
    """Return only shelters whose operational fields are actually known.

    The frozen shelter contract requires coordinates, total capacity and current
    occupancy. Unknown values are not replaced with zero. Resource sub-capacities
    may still remain unknown and are handled by the carrying-capacity engine as
    PARTIAL/UNVALIDATED.
    """
    required = {
        "shelter_id",
        "name",
        "latitude",
        "longitude",
        "total_capacity",
        "current_occupancy",
    }
    missing = sorted(required - set(staged.columns))
    if missing:
        raise ValueError(
            "pilot shelters are not application-ready; authoritative enrichment is still required for: "
            + ", ".join(missing)
        )

    ready = staged.dropna(
        subset=["latitude", "longitude", "total_capacity", "current_occupancy"]
    ).copy()
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
