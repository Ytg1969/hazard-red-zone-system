RESOURCE_CAPACITY_FIELDS = (
    "water_capacity",
    "sanitation_capacity",
    "access_capacity",
)


def _non_negative_number(value, field_name: str) -> float:
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc


def calculate_capacity(shelter: dict) -> dict:
    """Calculate effective and available shelter capacity.

    Rules:
    - total_capacity is always the physical fallback ceiling.
    - If all resource sub-capacities are available, the result is VALIDATED.
    - If only some resource sub-capacities are available, the minimum known
      constraint is used and the result is PARTIAL.
    - If no resource sub-capacities are available, total_capacity is used and
      the result is UNVALIDATED.
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

    if known_resource_capacities:
        effective = min([total, *known_resource_capacities.values()])
        validation_status = (
            "VALIDATED" if not missing_resource_fields else "PARTIAL"
        )
    else:
        effective = total
        validation_status = "UNVALIDATED"

    available = max(0.0, effective - current)

    return {
        "effective_capacity": round(effective, 2),
        "available_capacity": round(available, 2),
        "current_occupancy": round(current, 2),
        "capacity_validation_status": validation_status,
        "known_resource_capacities": known_resource_capacities,
        "missing_resource_fields": missing_resource_fields,
    }
