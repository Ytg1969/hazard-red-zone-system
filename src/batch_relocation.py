"""System-wide capacity-safe relocation planning across multiple habitations.

This module adapts the teammate prototype's useful global-allocation idea while
preserving the project's existing safety filters, carrying-capacity model and
explainable shelter ranking. It intentionally avoids claiming a mathematically
optimal solution; the algorithm is deterministic and priority-first.
"""
from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.relocation import rank_shelters


DEFAULT_PRIORITIES = ("IMMEDIATE", "SHORT_TERM")
_PRIORITY_ORDER = {
    "IMMEDIATE": 0,
    "SHORT_TERM": 1,
    "MEDIUM_TERM": 2,
    "MONITOR": 3,
}


def plan_batch_relocation(
    habitations: pd.DataFrame,
    shelters: pd.DataFrame,
    *,
    priorities: Iterable[str] = DEFAULT_PRIORITIES,
) -> dict:
    """Allocate multiple priority habitations without double-booking capacity.

    Habitations are processed by relocation priority and then descending risk.
    For each habitation, the existing shelter ranking engine is recomputed using
    the shelter occupancy after all earlier assignments. This means every
    assignment respects the same minimum-safety filter and limiting-resource
    capacity logic used by the single-habitation Relocation Planner.

    Returns a dictionary containing allocation rows, explicit deficits and
    aggregate population totals. Population may be split across shelters.
    """
    if not isinstance(habitations, pd.DataFrame) or not isinstance(shelters, pd.DataFrame):
        raise TypeError("habitations and shelters must be pandas DataFrames")

    selected_priorities = {str(value).upper() for value in priorities}
    if not selected_priorities:
        raise ValueError("at least one relocation priority must be selected")

    work_habitations = habitations.copy()
    work_shelters = shelters.copy()
    if work_habitations.empty:
        return {
            "required_population": 0,
            "allocated_population": 0,
            "remaining_deficit": 0,
            "allocations": [],
            "unallocated": [],
        }
    if work_shelters.empty:
        required = int(
            pd.to_numeric(
                work_habitations.loc[
                    work_habitations["relocation_priority"].astype(str).str.upper().isin(selected_priorities),
                    "population",
                ],
                errors="coerce",
            )
            .fillna(0)
            .clip(lower=0)
            .sum()
        )
        return {
            "required_population": required,
            "allocated_population": 0,
            "remaining_deficit": required,
            "allocations": [],
            "unallocated": [],
        }

    if "relocation_priority" not in work_habitations.columns:
        raise ValueError("habitations must include relocation_priority")
    if "risk_score" not in work_habitations.columns:
        raise ValueError("habitations must include risk_score")
    if "population" not in work_habitations.columns:
        raise ValueError("habitations must include population")
    if "current_occupancy" not in work_shelters.columns:
        raise ValueError("shelters must include current_occupancy")

    work_habitations["_priority_order"] = (
        work_habitations["relocation_priority"]
        .astype(str)
        .str.upper()
        .map(_PRIORITY_ORDER)
        .fillna(99)
    )
    selected = work_habitations[
        work_habitations["relocation_priority"].astype(str).str.upper().isin(selected_priorities)
    ].copy()
    selected = selected.sort_values(["_priority_order", "risk_score"], ascending=[True, False])

    mutable_shelters = work_shelters.to_dict(orient="records")
    allocations: list[dict] = []
    unallocated: list[dict] = []
    required_population = 0
    allocated_population = 0

    for habitation in selected.to_dict(orient="records"):
        required = max(0, int(float(habitation.get("population", 0) or 0)))
        remaining = required
        required_population += required

        while remaining > 0:
            ranking_input = habitation.copy()
            ranking_input["population"] = remaining
            ranked = rank_shelters(ranking_input, mutable_shelters)
            if not ranked:
                break

            candidate = ranked[0]
            available = max(0, int(float(candidate.get("available_capacity", 0) or 0)))
            if available <= 0:
                break

            assigned = min(remaining, available)
            shelter_id = candidate.get("shelter_id")
            shelter_record = next(
                (
                    item
                    for item in mutable_shelters
                    if str(item.get("shelter_id")) == str(shelter_id)
                ),
                None,
            )
            if shelter_record is None:
                raise RuntimeError(f"ranked shelter {shelter_id!r} was not found in the working inventory")

            shelter_record["current_occupancy"] = float(
                shelter_record.get("current_occupancy", 0) or 0
            ) + assigned

            allocations.append(
                {
                    "habitation_id": habitation.get("habitation_id"),
                    "habitation_name": habitation.get("name"),
                    "relocation_priority": habitation.get("relocation_priority"),
                    "risk_score": round(float(habitation.get("risk_score", 0) or 0), 2),
                    "shelter_id": shelter_id,
                    "shelter_name": candidate.get("shelter_name"),
                    "assigned_population": assigned,
                    "distance_km": candidate.get("distance_km"),
                    "suitability_score": candidate.get("suitability_score"),
                    "routing_mode": candidate.get("routing_mode"),
                    "capacity_validation_status": candidate.get("capacity_validation_status"),
                }
            )
            remaining -= assigned
            allocated_population += assigned

        if remaining > 0:
            unallocated.append(
                {
                    "habitation_id": habitation.get("habitation_id"),
                    "habitation_name": habitation.get("name"),
                    "relocation_priority": habitation.get("relocation_priority"),
                    "unallocated_population": remaining,
                    "reason": "Insufficient safe available shelter capacity",
                }
            )

    return {
        "required_population": required_population,
        "allocated_population": allocated_population,
        "remaining_deficit": required_population - allocated_population,
        "allocations": allocations,
        "unallocated": unallocated,
    }
