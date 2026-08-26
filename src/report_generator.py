def generate_action_plan(habitation: dict, risk: dict, relocation: dict | None) -> str:
    lines = [
        "# Draft Disaster Response Action Plan",
        "",
        f"Habitation: {habitation.get('name', 'Unknown')}",
        f"Risk: {risk.get('risk_score', '—')} / {risk.get('risk_level', '—')}",
        f"Population: {habitation.get('population', '—')}",
    ]
    if relocation:
        lines.extend([
            f"Recommended shelter: {relocation.get('shelter_name', '—')}",
            f"Distance: {relocation.get('distance_km', '—')} km",
            f"Available capacity: {relocation.get('available_capacity', '—')}",
        ])
    else:
        lines.append("Recommended shelter: No valid candidate available")

    lines.extend([
        "",
        "Disclaimer: This prototype provides decision support only. Final evacuation and relocation orders remain with authorized authorities.",
    ])
    return "\n".join(lines)
