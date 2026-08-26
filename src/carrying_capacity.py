def calculate_capacity(shelter: dict) -> dict:
    total = max(0.0, float(shelter.get("total_capacity", 0)))
    current = max(0.0, float(shelter.get("current_occupancy", 0)))

    limiting = [total]
    for key in ("water_capacity", "sanitation_capacity", "access_capacity"):
        value = shelter.get(key)
        if value is not None and value != "":
            limiting.append(max(0.0, float(value)))

    effective = min(limiting) if limiting else 0.0
    available = max(0.0, effective - current)

    return {
        "effective_capacity": round(effective, 2),
        "available_capacity": round(available, 2),
        "current_occupancy": round(current, 2),
    }
