"""System-wide capacity-safe relocation planning across multiple habitations.

The planner is deterministic and priority-first. It preserves the existing
safety filters and carrying-capacity model and never double-books shelter space.
When demo_city is present on both contracts, assignments are constrained to the
same city so a multi-city demonstration cannot route people across states.
"""
from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from src.relocation import rank_shelters

DEFAULT_PRIORITIES = ("IMMEDIATE", "SHORT_TERM")
_PRIORITY_ORDER = {"IMMEDIATE": 0, "SHORT_TERM": 1, "MEDIUM_TERM": 2, "MONITOR": 3}


def plan_batch_relocation(habitations: pd.DataFrame, shelters: pd.DataFrame, *, priorities: Iterable[str] = DEFAULT_PRIORITIES) -> dict:
    if not isinstance(habitations, pd.DataFrame) or not isinstance(shelters, pd.DataFrame):
        raise TypeError("habitations and shelters must be pandas DataFrames")
    selected_priorities = {str(value).upper() for value in priorities}
    if not selected_priorities:
        raise ValueError("at least one relocation priority must be selected")

    work_habitations = habitations.copy()
    work_shelters = shelters.copy()
    if "relocation_priority" not in work_habitations.columns:
        raise ValueError("habitations must include relocation_priority")
    if "risk_score" not in work_habitations.columns:
        raise ValueError("habitations must include risk_score")
    if "population" not in work_habitations.columns:
        raise ValueError("habitations must include population")
    if not work_shelters.empty and "current_occupancy" not in work_shelters.columns:
        raise ValueError("shelters must include current_occupancy")

    work_habitations["_priority_order"] = work_habitations["relocation_priority"].astype(str).str.upper().map(_PRIORITY_ORDER).fillna(99)
    selected = work_habitations[work_habitations["relocation_priority"].astype(str).str.upper().isin(selected_priorities)].copy()
    selected = selected.sort_values(["_priority_order", "risk_score"], ascending=[True, False])

    required_population = int(pd.to_numeric(selected["population"], errors="coerce").fillna(0).clip(lower=0).sum())
    if selected.empty:
        return {"required_population": 0, "allocated_population": 0, "remaining_deficit": 0, "allocations": [], "unallocated": []}
    if work_shelters.empty:
        return {"required_population": required_population, "allocated_population": 0, "remaining_deficit": required_population, "allocations": [], "unallocated": []}

    mutable_shelters = work_shelters.to_dict(orient="records")
    constrain_city = "demo_city" in work_habitations.columns and "demo_city" in work_shelters.columns
    allocations: list[dict] = []
    unallocated: list[dict] = []
    allocated_population = 0

    for habitation in selected.to_dict(orient="records"):
        remaining = max(0, int(float(habitation.get("population", 0) or 0)))
        while remaining > 0:
            ranking_input = habitation.copy()
            ranking_input["population"] = remaining
            local_inventory = mutable_shelters
            if constrain_city and habitation.get("demo_city"):
                local_inventory = [item for item in mutable_shelters if item.get("demo_city") == habitation.get("demo_city")]
            ranked = rank_shelters(ranking_input, local_inventory)
            if not ranked:
                break
            candidate = ranked[0]
            available = max(0, int(float(candidate.get("available_capacity", 0) or 0)))
            if available <= 0:
                break
            assigned = min(remaining, available)
            shelter_id = candidate.get("shelter_id")
            shelter_record = next((item for item in mutable_shelters if str(item.get("shelter_id")) == str(shelter_id)), None)
            if shelter_record is None:
                raise RuntimeError(f"ranked shelter {shelter_id!r} was not found in the working inventory")
            shelter_record["current_occupancy"] = float(shelter_record.get("current_occupancy", 0) or 0) + assigned
            allocations.append({
                "habitation_id": habitation.get("habitation_id"),
                "habitation_name": habitation.get("name"),
                "demo_city": habitation.get("demo_city"),
                "relocation_priority": habitation.get("relocation_priority"),
                "risk_score": round(float(habitation.get("risk_score", 0) or 0), 2),
                "shelter_id": shelter_id,
                "shelter_name": candidate.get("shelter_name"),
                "assigned_population": assigned,
                "distance_km": candidate.get("distance_km"),
                "suitability_score": candidate.get("suitability_score"),
                "routing_mode": candidate.get("routing_mode"),
                "capacity_validation_status": candidate.get("capacity_validation_status"),
            })
            remaining -= assigned
            allocated_population += assigned
        if remaining > 0:
            unallocated.append({
                "habitation_id": habitation.get("habitation_id"),
                "habitation_name": habitation.get("name"),
                "demo_city": habitation.get("demo_city"),
                "relocation_priority": habitation.get("relocation_priority"),
                "unallocated_population": remaining,
                "reason": "Insufficient safe available shelter capacity in the applicable geography",
            })

    return {
        "required_population": required_population,
        "allocated_population": allocated_population,
        "remaining_deficit": required_population - allocated_population,
        "allocations": allocations,
        "unallocated": unallocated,
    }
