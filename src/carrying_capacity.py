RESOURCE_CAPACITY_FIELDS = (
    "water_capacity",
    "sanitation_capacity",
    "access_capacity",
)

RESOURCE_LABELS = {
    "total_capacity": "Physical space",
    "water_capacity": "Water",
    "sanitation_capacity": "Sanitation",
    "access_capacity": "Access / logistics",
}


def _non_negative_number(value, field_name: str) -> float:
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc


def calculate_capacity(shelter: dict) -> dict:
    """Calculate effective/available capacity and explain the limiting evidence.

    Frozen rules remain unchanged:
    - total_capacity is always the physical fallback ceiling.
    - all resource sub-capacities known -> VALIDATED;
    - some known -> minimum known constraint / PARTIAL;
    - none known -> total_capacity / UNVALIDATED;
    - available capacity never becomes negative.

    Additional fields are diagnostic only. They make the limiting resource and
    evidence completeness visible to operators without changing the capacity
    decision itself.
    """
    total = _non_negative_number(shelter.get("total_capacity", 0), "total_capacity")
    current = _non_negative_number(
        shelter.get("current_occupancy", 0), "current_occupancy"
    )

    known_resource_capacities: dict[str, float] = {}
    missing_resource_fields: list[str] = []

    for field in RESOURCE_CAPACITY_FIELDS:
        value = shelter.get(field)
        if value is None or value == "":
            missing_resource_fields.append(field)
            continue
        known_resource_capacities[field] = _non_negative_number(value, field)

    candidate_capacities = {"total_capacity": total, **known_resource_capacities}
    limiting_resource = min(candidate_capacities, key=candidate_capacities.get)

    if known_resource_capacities:
        effective = candidate_capacities[limiting_resource]
        validation_status = (
            "VALIDATED" if not missing_resource_fields else "PARTIAL"
        )
    else:
        effective = total
        validation_status = "UNVALIDATED"

    available = max(0.0, effective - current)
    utilization_pct = (current / effective * 100.0) if effective > 0 else (100.0 if current > 0 else 0.0)
    evidence_completeness_pct = (
        len(known_resource_capacities) / len(RESOURCE_CAPACITY_FIELDS) * 100.0
    )

    return {
        "effective_capacity": round(effective, 2),
        "available_capacity": round(available, 2),
        "current_occupancy": round(current, 2),
        "capacity_validation_status": validation_status,
        "known_resource_capacities": known_resource_capacities,
        "missing_resource_fields": missing_resource_fields,
        "limiting_resource": limiting_resource,
        "limiting_resource_label": RESOURCE_LABELS[limiting_resource],
        "limiting_capacity": round(candidate_capacities[limiting_resource], 2),
        "capacity_evidence_completeness_pct": round(evidence_completeness_pct, 1),
        "capacity_utilization_pct": round(utilization_pct, 1),
    }
