from datetime import datetime, timezone


def generate_action_plan(
    habitation: dict,
    risk: dict,
    relocation: dict | None,
    allocation: dict | None = None,
    data_mode: str = "DEMO",
) -> str:
    """Generate a professional Markdown decision-support action plan."""
    generated_at = datetime.now(timezone.utc).isoformat()
    lines = [
        "# Draft Disaster Response Action Plan",
        "",
        f"Generated: {generated_at}",
        f"Data mode: {str(data_mode).upper()}",
        "",
        "## Affected Habitation",
        f"- Habitation: {habitation.get('name', 'Unknown')}",
        f"- Habitation ID: {habitation.get('habitation_id', '—')}",
        f"- Population: {habitation.get('population', '—')}",
        f"- Children: {habitation.get('children_population', '—')}",
        f"- Elderly: {habitation.get('elderly_population', '—')}",
        f"- Relocation priority: {habitation.get('relocation_priority', '—')}",
        "",
        "## Risk Assessment",
        f"- Risk score: {risk.get('risk_score', '—')} / 100",
        f"- Risk level: {risk.get('risk_level', '—')}",
        f"- Primary drivers: {', '.join(risk.get('drivers', [])) or '—'}",
    ]

    lines.extend(["", "## Primary Relocation Recommendation"])
    if relocation:
        lines.extend(
            [
                f"- Recommended shelter: {relocation.get('shelter_name', '—')}",
                f"- Distance: {relocation.get('distance_km', '—')} km",
                f"- Travel time: {relocation.get('travel_time_min') or 'Not available in fallback routing'}",
                f"- Routing mode: {relocation.get('routing_mode', '—')}",
                f"- Available capacity: {relocation.get('available_capacity', '—')}",
                f"- Capacity validation: {relocation.get('capacity_validation_status', '—')}",
                f"- Suitability score: {relocation.get('suitability_score', '—')} / 100",
            ]
        )
    else:
        lines.append("- No valid safe shelter candidate is currently available.")

    if allocation is not None:
        lines.extend(
            [
                "",
                "## Capacity Allocation",
                f"- Required population: {allocation.get('required_population', '—')}",
                f"- Allocated population: {allocation.get('allocated_population', '—')}",
                f"- Remaining capacity deficit: {allocation.get('remaining_deficit', '—')}",
            ]
        )
        for item in allocation.get("allocations", []):
            lines.append(
                f"- {item.get('shelter_name', 'Shelter')}: assign {item.get('assigned_population', '—')} people "
                f"({item.get('distance_km', '—')} km, suitability {item.get('suitability_score', '—')}/100)"
            )

    lines.extend(
        [
            "",
            "## Operational Notes",
            "- Confirm current road conditions before dispatch.",
            "- Revalidate shelter occupancy and essential-resource capacity before movement.",
            "- Prioritize vulnerable groups according to local disaster-management protocols.",
            "",
            "---",
            "**Decision-support disclaimer:** This prototype does not issue an official evacuation order. "
            "Final evacuation, relocation and emergency decisions remain with authorized government authorities.",
        ]
    )
    return "\n".join(lines)
