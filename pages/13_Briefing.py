from __future__ import annotations

import json
from datetime import datetime, timezone

import streamlit as st

from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import (
    inject_global_css,
    render_command_card,
    render_context_bar,
    render_data_mode_indicator,
    render_decision_gate,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
    render_section_header,
)

st.set_page_config(page_title="Incident Briefing", page_icon="BR", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
render_page_header(
    "Incident Briefing",
    "A concise administrative handoff with the incident picture, unresolved constraints, provenance and exportable priority register.",
)

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds could not be activated: {exc}")

if resolved:
    payload = resolved["payload"]
    habitations_raw = resolved["habitations"]
    shelters_raw = resolved["shelters"]
    label = str(payload.get("label", "Operational dataset"))
    mode = str(payload.get("habitation_mode", "UNVERIFIED")).upper()
    with st.sidebar:
        st.markdown("### Brief scope")
        st.success(label)
        hazard_profile = st.selectbox(
            "Hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: "Stored / calibrated GIS" if value == "stored" else value.title(),
        )
else:
    city, hazard_profile = render_demo_scope_controls("brief")
    habitations_raw, shelters_raw = load_demo_data(city)
    label = city
    mode = "DEMO"

try:
    habitations = enrich_habitations(
        habitations_raw,
        hazard_data=None,
        hazard_type=hazard_profile,
        add_coordination_zones=False,
    )
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
except Exception as exc:
    st.error(f"Unable to build incident briefing: {exc}")
    render_disclaimer()
    st.stop()

priority = habitations.sort_values("risk_score", ascending=False)
top = priority.iloc[0]
focus_name = st.session_state.get("focus_location")
focus_rows = priority[priority["name"].astype(str) == str(focus_name)] if focus_name else priority.iloc[0:0]
focus = focus_rows.iloc[0] if not focus_rows.empty else top
available_capacity = int(summary["available_shelter_capacity"])
immediate = int(summary["immediate_relocation_population"])
capacity_gap = max(0, immediate - available_capacity)
generated_at = datetime.now(timezone.utc).isoformat()

render_context_bar(
    label,
    f"{hazard_profile.replace('_', ' ').title()} · {mode}",
    "ADMINISTRATIVE HANDOFF",
)
if mode in {"LIVE", "CACHED", "DEMO"}:
    render_data_mode_indicator(mode)
else:
    st.warning("Workspace provenance is unverified.")

render_kpi_strip([
    ("People at risk", f"{int(summary['population_at_risk']):,}", "HIGH + CRITICAL"),
    ("Critical zones", f"{int(summary['critical_red_zones']):,}", "Analytical classification"),
    ("Immediate relocation", f"{immediate:,}", "Decision-support priority"),
    ("Available capacity", f"{available_capacity:,}", "Safety + limiting-resource constraints"),
    ("Capacity gap", f"{capacity_gap:,}", "Uncovered demand" if capacity_gap else "No current gap"),
])

render_section_header(
    "Situation handoff",
    "The brief surfaces the highest analytical priority and any capacity issue before export.",
    "REVIEW BEFORE USE",
)
left, right = st.columns([1.7, 1], gap="large")
with left:
    render_command_card(
        "Highest analytical priority",
        str(top["name"]),
        f"{float(top['risk_score']):.1f}/100 risk · {int(top['population']):,} people · {top['relocation_priority']} relocation priority",
        severity=str(top["risk_level"]),
    )
    render_risk_badge(top["risk_level"])
    st.write(f"**Primary drivers** · {top['risk_drivers']}")
    if str(focus["name"]) != str(top["name"]):
        st.caption(f"Current operator focus: {focus['name']} · {float(focus['risk_score']):.1f}/100")

with right:
    render_decision_gate(
        "Capacity status",
        f"{available_capacity:,} available against {immediate:,} immediate demand",
        "danger" if capacity_gap else "ok",
    )
    render_decision_gate(
        "Authority boundary",
        "This briefing is decision support and is not an automated evacuation order.",
        "ok",
    )
    render_decision_gate(
        "Source review",
        f"Active data mode: {mode}. Confirm provenance before operational use.",
        "warn" if mode not in {"LIVE", "CACHED"} else "ok",
    )

render_section_header(
    "Priority register",
    "Keep the handoff compact; the detailed explanation and route evidence remain in their dedicated workspaces.",
    "TOP 8",
)
cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority"] if c in priority.columns]
st.dataframe(priority[cols].head(8), width="stretch", hide_index=True)

brief = {
    "generated_at_utc": generated_at,
    "scope": label,
    "mode": mode,
    "hazard_profile": hazard_profile,
    "summary": {
        "habitations_monitored": int(summary["habitations_monitored"]),
        "critical_red_zones": int(summary["critical_red_zones"]),
        "population_at_risk": int(summary["population_at_risk"]),
        "immediate_relocation_population": immediate,
        "available_shelter_capacity": available_capacity,
        "capacity_gap": capacity_gap,
    },
    "highest_priority": {
        "name": str(top["name"]),
        "risk_score": float(top["risk_score"]),
        "risk_level": str(top["risk_level"]),
        "population": int(top["population"]),
        "relocation_priority": str(top["relocation_priority"]),
        "risk_drivers": str(top["risk_drivers"]),
    },
    "safety_contract": {
        "risk_equation": "Risk = 0.35H + 0.25E + 0.25V + 0.15A",
        "external_context_mutates_baseline_risk": False,
        "shelter_capacity_is_hard_constraint": True,
        "automated_evacuation_order": False,
    },
}

render_section_header(
    "Export handoff",
    "Use machine-readable JSON for system handoff or CSV for a compact priority register.",
    "EXPORT",
)
export_left, export_right = st.columns(2, gap="large")
with export_left:
    st.download_button(
        "Download briefing JSON",
        data=json.dumps(brief, indent=2).encode("utf-8"),
        file_name=f"hazard_command_brief_{str(label).lower().replace(' ', '_')}.json",
        mime="application/json",
        width="stretch",
    )
with export_right:
    csv_cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"] if c in priority.columns]
    st.download_button(
        "Download priority CSV",
        data=priority[csv_cols].to_csv(index=False).encode("utf-8"),
        file_name=f"hazard_command_priority_{str(label).lower().replace(' ', '_')}.csv",
        mime="text/csv",
        width="stretch",
    )

with st.expander("Evidence & assumptions", expanded=False):
    st.code("Risk = 0.35H + 0.25E + 0.25V + 0.15A")
    st.caption("External live context remains additive/corroborative unless a source-specific calibration has been explicitly approved.")
    st.caption("Shelter safety and available capacity remain hard constraints. Unknown operational values are not silently replaced with zero.")

render_disclaimer()
