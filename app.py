from __future__ import annotations

import streamlit as st

from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import (
    RISK_COLORS,
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

DEPLOYMENT_RELEASE = "HC2-2026-09-07-r2"

st.set_page_config(
    page_title="Hazard Command",
    page_icon="HZ",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_global_css()
render_page_header(
    "Incident Command",
    "A single decision surface for risk, exposed population, safe capacity and the next review action.",
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
    active_label = str(payload.get("label", "Operational dataset"))
    active_mode = str(payload.get("habitation_mode", "UNVERIFIED")).upper()
    with st.sidebar:
        st.markdown("### Analytical context")
        st.success(active_label)
        hazard_profile = st.selectbox(
            "Hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: "Stored / calibrated GIS" if value == "stored" else value.replace("_", " ").title(),
            key="command_operational_hazard",
        )
    mode_label = active_mode if active_mode in {"LIVE", "CACHED", "DEMO"} else "UNVERIFIED"
else:
    city, hazard_profile = render_demo_scope_controls("command")
    habitations_raw, shelters_raw = load_demo_data(city)
    active_label = city
    active_mode = "DEMO"
    mode_label = "DEMO"

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
    st.error(f"The active analytical data could not be prepared: {exc}")
    render_disclaimer()
    st.stop()

priority = habitations.sort_values("risk_score", ascending=False).copy()
if priority.empty:
    st.error("No habitation records are available in the active scope.")
    render_disclaimer()
    st.stop()

focus_options = priority["name"].astype(str).tolist()
with st.sidebar:
    st.markdown("### Focus")
    default_focus = st.session_state.get("focus_location")
    default_index = focus_options.index(default_focus) if default_focus in focus_options else 0
    focus_name = st.selectbox("Priority location", focus_options, index=default_index, key="command_focus")
    st.session_state["focus_location"] = focus_name
    st.caption("The focus is carried as session context for the operator workflow.")

focus = priority.loc[priority["name"].astype(str) == str(focus_name)].iloc[0]
critical = priority[priority["risk_level"] == "CRITICAL"]
high = priority[priority["risk_level"] == "HIGH"]
immediate = int(summary["immediate_relocation_population"])
available_capacity = int(summary["available_shelter_capacity"])
capacity_gap = max(0, immediate - available_capacity)
coverage_pct = 100.0 if immediate <= 0 else min(100.0, available_capacity / immediate * 100.0)

render_context_bar(
    active_label,
    f"{hazard_profile.replace('_', ' ').title()} · {mode_label}",
    f"Release {DEPLOYMENT_RELEASE}",
)
if active_mode in {"LIVE", "CACHED", "DEMO"}:
    render_data_mode_indicator(active_mode)
else:
    st.warning("Active workspace provenance is UNVERIFIED; treat operational values as unverified until reviewed.")

render_kpi_strip([
    ("People at risk", f"{int(summary['population_at_risk']):,}", "HIGH + CRITICAL population"),
    ("Critical zones", f"{len(critical):,}", f"{len(high):,} additional HIGH zones"),
    ("Relocate now", f"{immediate:,}", "Immediate decision-support priority"),
    ("Safe capacity", f"{available_capacity:,}", f"{coverage_pct:.0f}% of immediate demand"),
    ("Capacity gap", f"{capacity_gap:,}", "Uncovered immediate demand" if capacity_gap else "Immediate demand currently covered"),
])

render_section_header(
    "Decision board",
    "Focus one location, verify why it is risky, then validate capacity and routing before any administrative decision.",
    "ACTIVE INCIDENT",
)
main_col, gate_col = st.columns([2.05, 1], gap="large")

with main_col:
    severity = str(focus["risk_level"]).upper()
    render_command_card(
        "Priority focus",
        str(focus["name"]),
        f"{int(focus['population']):,} people · {float(focus['risk_score']):.1f}/100 risk · {str(focus['relocation_priority']).replace('_', ' ')} priority",
        severity=severity,
    )
    badge_col, risk_col, evidence_col = st.columns([.72, 1, 1.2], gap="small")
    with badge_col:
        render_risk_badge(severity)
    with risk_col:
        st.metric("Risk score", f"{float(focus['risk_score']):.1f}/100")
    with evidence_col:
        completeness = float(focus.get("hazard_data_completeness", 0) or 0)
        st.metric("Evidence", f"{completeness:.0f}%", help="Hazard evidence completeness for the selected location")

    st.markdown(f"**Dominant drivers** · {focus['risk_drivers']}")
    completeness = float(focus.get("hazard_data_completeness", 0) or 0)
    st.progress(max(0.0, min(1.0, completeness / 100.0)), text=f"Evidence completeness {completeness:.0f}%")

    if severity == "CRITICAL":
        st.error("CRITICAL analytical risk. Validate shelter safety, available capacity and route evidence before escalation.")
    elif severity == "HIGH":
        st.warning("HIGH analytical risk. Continue through risk explanation and relocation review.")
    else:
        st.info("Selected location is below HIGH risk in the current analytical scope. Continue monitoring and evidence review.")

with gate_col:
    st.markdown("#### Decision gates")
    render_decision_gate(
        "Analytical risk available",
        f"Risk = 0.35H + 0.25E + 0.25V + 0.15A · selected score {float(focus['risk_score']):.1f}",
        "danger" if severity == "CRITICAL" else "warn" if severity == "HIGH" else "ok",
    )
    render_decision_gate(
        "Capacity check",
        f"{available_capacity:,} safe places available against {immediate:,} immediate demand",
        "danger" if capacity_gap else "ok",
    )
    render_decision_gate(
        "Authority boundary",
        "Decision support only; the application does not issue evacuation orders.",
        "ok",
    )
    st.markdown("#### Continue workflow")
    st.page_link("pages/2_Red_Zone_Map.py", label="◉  Inspect spatial picture", use_container_width=True)
    st.page_link("pages/3_Risk_Analysis.py", label="◒  Explain selected risk", use_container_width=True)
    st.page_link("pages/4_Relocation_Planner.py", label="⇢  Build relocation plan", use_container_width=True)
    st.page_link("pages/13_Briefing.py", label="▤  Generate incident briefing", use_container_width=True)

render_section_header(
    "Priority register",
    "A compact queue for operator triage; deeper evidence stays in Risk Intelligence and the map.",
    f"{len(priority)} LOCATIONS",
)
register_tab, distribution_tab = st.tabs(["Priority queue", "Risk mix"])
with register_tab:
    queue_cols = [
        c
        for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"]
        if c in priority.columns
    ]
    st.dataframe(
        priority[queue_cols].head(10),
        width="stretch",
        hide_index=True,
        column_config={
            "risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%.1f"),
            "population": st.column_config.NumberColumn("Population", format=",%d"),
        },
    )
with distribution_tab:
    levels = ["CRITICAL", "HIGH", "MODERATE", "LOW"]
    columns = st.columns(4, gap="small")
    for column, level in zip(columns, levels):
        count = int((priority["risk_level"] == level).sum())
        population = int(priority.loc[priority["risk_level"] == level, "population"].sum())
        color = RISK_COLORS[level]
        with column:
            st.markdown(
                f"<div class='hz-card' style='border-top:2px solid {color}'>"
                f"<div class='label'>{level}</div>"
                f"<div class='value'>{count} locations</div>"
                f"<div class='detail'>{population:,} people</div>"
                "</div>",
                unsafe_allow_html=True,
            )

with st.expander("Evidence and technical controls", expanded=False):
    st.caption("Secondary tools are intentionally removed from the primary decision flow.")
    tool_cols = st.columns(4, gap="small")
    links = [
        ("Evidence Center", "pages/14_Evidence_Center.py"),
        ("Operational Data", "pages/9_Operational_Data.py"),
        ("System Readiness", "pages/8_System_Readiness.py"),
        ("System Boundaries", "pages/15_About_System.py"),
    ]
    for col, (label, path) in zip(tool_cols, links):
        with col:
            st.page_link(path, label=label, use_container_width=True)

render_disclaimer()
