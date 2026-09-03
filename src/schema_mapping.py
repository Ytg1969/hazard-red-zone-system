"""Explicit schema mapping for heterogeneous authority datasets.

Government/district exports rarely use the project's canonical field names.
This module keeps that adaptation transparent: operators can inspect suggested
matches and explicitly map source columns before production validation.
"""
from __future__ import annotations

import re
from typing import Mapping

import pandas as pd


HABITATION_FIELDS = (
    "habitation_id",
    "name",
    "latitude",
    "longitude",
    "population",
    "children_population",
    "elderly_population",
)

SHELTER_FIELDS = (
    "shelter_id",
    "name",
    "latitude",
    "longitude",
    "total_capacity",
    "current_occupancy",
)

ALIASES = {
    "habitation_id": {"habitation_id", "habitationid", "village_id", "village_code", "villagecode", "settlement_id", "settlementid", "lgd_code", "lgdcode", "location_id"},
    "shelter_id": {"shelter_id", "shelterid", "site_id", "siteid", "relocation_site_id", "relocationsiteid", "facility_id", "facilityid"},
    "name": {"name", "village_name", "villagename", "habitation_name", "habitationname", "settlement_name", "settlementname", "shelter_name", "sheltername", "site_name", "sitename", "facility_name", "facilityname"},
    "latitude": {"latitude", "lat", "y", "y_coord", "ycoord", "gps_lat", "gpslat"},
    "longitude": {"longitude", "lon", "lng", "long", "x", "x_coord", "xcoord", "gps_lon", "gpslon"},
    "population": {"population", "total_population", "totalpopulation", "pop", "tot_pop", "totpop", "persons", "population_total"},
    "children_population": {"children_population", "childrenpopulation", "child_population", "childpopulation", "children", "child_pop", "childpop", "age_0_6", "age06", "population_0_6"},
    "elderly_population": {"elderly_population", "elderlypopulation", "elderly", "senior_population", "seniorpopulation", "age_60_plus", "age60plus", "population_60_plus"},
    "total_capacity": {"total_capacity", "totalcapacity", "capacity", "max_capacity", "maxcapacity", "shelter_capacity", "sheltercapacity", "rated_capacity"},
    "current_occupancy": {"current_occupancy", "currentoccupancy", "occupancy", "occupied", "current_load", "currentload", "persons_occupied", "people_present"},
}


def normalize_column_name(value: object) -> str:
    text = str(value or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def canonical_fields(kind: str) -> tuple[str, ...]:
    normalized = str(kind).strip().lower()
    if normalized in {"habitation", "habitations", "settlement", "settlements"}:
        return HABITATION_FIELDS
    if normalized in {"shelter", "shelters", "site", "sites", "relocation"}:
        return SHELTER_FIELDS
    raise ValueError("kind must be habitation or shelter")


def suggest_field_mapping(df: pd.DataFrame, kind: str) -> dict[str, str | None]:
    """Suggest unambiguous source-column matches without modifying data."""
    fields = canonical_fields(kind)
    normalized_sources: dict[str, list[str]] = {}
    for column in df.columns:
        normalized_sources.setdefault(normalize_column_name(column), []).append(str(column))

    result: dict[str, str | None] = {}
    used: set[str] = set()
    for field in fields:
        candidates: list[str] = []
        for alias in ALIASES.get(field, {field}):
            candidates.extend(normalized_sources.get(normalize_column_name(alias), []))
        unique = [candidate for candidate in dict.fromkeys(candidates) if candidate not in used]
        if len(unique) == 1:
            result[field] = unique[0]
            used.add(unique[0])
        else:
            result[field] = None
    return result


def apply_field_mapping(df: pd.DataFrame, mapping: Mapping[str, str | None], kind: str) -> pd.DataFrame:
    """Rename explicitly selected source fields to the canonical contract.

    Existing canonical columns are preserved unless the mapping points to that
    same column. One source column cannot populate multiple canonical fields.
    """
    fields = set(canonical_fields(kind))
    unknown_targets = sorted(set(mapping) - fields)
    if unknown_targets:
        raise ValueError(f"mapping contains unsupported canonical fields: {unknown_targets}")

    selected = {target: str(source) for target, source in mapping.items() if source not in {None, ""}}
    missing_sources = sorted({source for source in selected.values() if source not in df.columns})
    if missing_sources:
        raise ValueError(f"mapping references missing source columns: {missing_sources}")

    sources = list(selected.values())
    if len(sources) != len(set(sources)):
        raise ValueError("one source column cannot map to multiple canonical fields")

    rename: dict[str, str] = {}
    for target, source in selected.items():
        if target in df.columns and source != target:
            raise ValueError(f"canonical column {target} already exists; remove it or map it to itself")
        rename[source] = target
    return df.rename(columns=rename).copy()


def missing_canonical_fields(df: pd.DataFrame, kind: str) -> list[str]:
    return [field for field in canonical_fields(kind) if field not in df.columns]
