from datetime import datetime, timezone
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _safe(value) -> str:
    return escape(str(value if value is not None else "-"))


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
                f"- Route status: {relocation.get('route_status', '—')}",
                f"- Route note: {relocation.get('route_note', '—') or '—'}",
                f"- Available capacity: {relocation.get('available_capacity', '—')}",
                f"- Capacity validation: {relocation.get('capacity_validation_status', '—')}",
                f"- Limiting capacity resource: {relocation.get('limiting_resource_label', '—')}",
                f"- Limiting capacity: {relocation.get('limiting_capacity', '—')}",
                f"- Capacity evidence completeness: {relocation.get('capacity_evidence_completeness_pct', '—')}%",
                f"- Capacity utilization: {relocation.get('capacity_utilization_pct', '—')}%",
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
            "- Route estimates do not currently include live traffic, road closures or hazard avoidance.",
            "",
            "---",
            "**Decision-support disclaimer:** This prototype does not issue an official evacuation order. "
            "Final evacuation, relocation and emergency decisions remain with authorized government authorities.",
        ]
    )
    return "\n".join(lines)


def generate_action_plan_pdf(
    habitation: dict,
    risk: dict,
    relocation: dict | None,
    allocation: dict | None = None,
    data_mode: str = "DEMO",
) -> bytes:
    """Generate a compact, browser-downloadable PDF action plan."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ActionPlanTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#163A5F"),
    )
    heading_style = ParagraphStyle(
        "ActionPlanHeading",
        parent=styles["Heading2"],
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#163A5F"),
    )
    body_style = ParagraphStyle(
        "ActionPlanBody",
        parent=styles["BodyText"],
        leading=14,
        spaceAfter=5,
    )
    disclaimer_style = ParagraphStyle(
        "ActionPlanDisclaimer",
        parent=body_style,
        fontSize=8,
        leading=10,
        textColor=colors.grey,
    )

    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
    story = [
        Paragraph("DRAFT DISASTER RESPONSE ACTION PLAN", title_style),
        Spacer(1, 4 * mm),
        Paragraph(f"Generated: {_safe(generated_at)} | Data mode: {_safe(str(data_mode).upper())}", body_style),
    ]

    summary_rows = [
        ["Habitation", str(habitation.get("name", "Unknown"))],
        ["Habitation ID", str(habitation.get("habitation_id", "-"))],
        ["Population", str(habitation.get("population", "-"))],
        ["Risk score", f"{risk.get('risk_score', '-')} / 100"],
        ["Risk level", str(risk.get("risk_level", "-"))],
        ["Relocation priority", str(habitation.get("relocation_priority", "-"))],
        ["Primary drivers", ", ".join(risk.get("drivers", [])) or "-"],
    ]
    summary = Table(summary_rows, colWidths=[52 * mm, 118 * mm])
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2F8")),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([Spacer(1, 4 * mm), summary])

    story.append(Paragraph("Primary Relocation Recommendation", heading_style))
    if relocation:
        story.extend(
            [
                Paragraph(f"Recommended shelter: <b>{_safe(relocation.get('shelter_name', '-'))}</b>", body_style),
                Paragraph(
                    f"Distance: {_safe(relocation.get('distance_km', '-'))} km | "
                    f"Travel time: {_safe(relocation.get('travel_time_min') or 'fallback routing only')} | "
                    f"Routing mode: {_safe(relocation.get('routing_mode', '-'))} | "
                    f"Route status: {_safe(relocation.get('route_status', '-'))}",
                    body_style,
                ),
                Paragraph(
                    f"Route note: {_safe(relocation.get('route_note') or '-')}",
                    body_style,
                ),
                Paragraph(
                    f"Available capacity: {_safe(relocation.get('available_capacity', '-'))} | "
                    f"Capacity status: {_safe(relocation.get('capacity_validation_status', '-'))} | "
                    f"Suitability: {_safe(relocation.get('suitability_score', '-'))} / 100",
                    body_style,
                ),
                Paragraph(
                    f"Limiting resource: {_safe(relocation.get('limiting_resource_label', '-'))} | "
                    f"Limiting capacity: {_safe(relocation.get('limiting_capacity', '-'))} | "
                    f"Evidence completeness: {_safe(relocation.get('capacity_evidence_completeness_pct', '-'))}% | "
                    f"Utilization: {_safe(relocation.get('capacity_utilization_pct', '-'))}%",
                    body_style,
                ),
            ]
        )
    else:
        story.append(Paragraph("No valid safe shelter candidate is currently available.", body_style))

    if allocation is not None:
        story.append(Paragraph("Capacity Allocation", heading_style))
        story.append(
            Paragraph(
                f"Required population: {_safe(allocation.get('required_population', '-'))} | "
                f"Allocated: {_safe(allocation.get('allocated_population', '-'))} | "
                f"Remaining deficit: {_safe(allocation.get('remaining_deficit', '-'))}",
                body_style,
            )
        )
        for item in allocation.get("allocations", []):
            story.append(
                Paragraph(
                    f"- {_safe(item.get('shelter_name', 'Shelter'))}: assign "
                    f"{_safe(item.get('assigned_population', '-'))} people "
                    f"({_safe(item.get('distance_km', '-'))} km; suitability "
                    f"{_safe(item.get('suitability_score', '-'))} / 100)",
                    body_style,
                )
            )

    story.extend(
        [
            Paragraph("Operational Notes", heading_style),
            Paragraph("- Confirm current road conditions before dispatch.", body_style),
            Paragraph("- Revalidate shelter occupancy and essential-resource capacity before movement.", body_style),
            Paragraph("- Prioritize vulnerable groups according to local disaster-management protocols.", body_style),
            Paragraph("- Route estimates do not currently include live traffic, road closures or hazard avoidance.", body_style),
            Spacer(1, 4 * mm),
            Paragraph(
                "Decision-support prototype only. Final evacuation, relocation and emergency decisions remain with authorized government authorities.",
                disclaimer_style,
            ),
        ]
    )

    document.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    if not pdf_bytes.startswith(b"%PDF"):
        raise ValueError("ReportLab did not produce a valid PDF payload")
    return pdf_bytes
