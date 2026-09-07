from __future__ import annotations

import streamlit as st

from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import (
    RISK_COLORS,
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
    render_source_card,
)

st.set_page_config(
    page_title="Hazard Command",
    page_icon="HZ",
    layout="wide",
    initial_sidebar_state="auto",
)
inject_global_css()
render_page_header(
    "Hazard Command",
    "One operational picture for danger, people, shelter capacity and the next safe action.",
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
    active_label = payload.get("label", "Operational dataset")
    active_mode = str(payload.get("habitation_mode", "UNVERIFIED")).upper()
    with st.sidebar:
        st.markdown("### Incident scope")
        st.success(active_label)
        hazard_profile = st.selectbox(
            "Hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: "Stored / calibrated GIS" if value == "stored" else value.replace("_", " ").title(),
            key="command_operational_hazard",
        )
    if active_mode in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(active_mode)
    else:
        st.warning("Active workspace provenance is unverified.")
    context_caption = f"{active_label} · {hazard_profile.replace('_', ' ').title()}"
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("command")
    habitations_raw, shelters_raw = load_demo_data(city)
    active_label = city
    context_caption = f"{city} · {hazard_profile.replace('_', ' ').title()} · demonstration scenario"

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
top = priority.iloc[0]
critical = priority[priority["risk_level"] == "CRITICAL"]
high = priority[priority["risk_level"] == "HIGH"]
at_risk_population = int(summary["population_at_risk"])
available_capacity = int(summary["available_shelter_capacity"])
capacity_gap = max(0, int(summary["immediate_relocation_population"]) - available_capacity)
coverage_pct = 100.0 if int(summary["immediate_relocation_population"]) <= 0 else min(
    100.0,
    available_capacity / int(summary["immediate_relocation_population"]) * 100.0,
)

st.caption(context_caption)
render_kpi_strip([
    ("People at risk", f"{at_risk_population:,}", "HIGH + CRITICAL population"),
    ("Critical zones", f"{len(critical):,}", f"{len(high):,} additional HIGH zones"),
    ("Relocate now", f"{int(summary['immediate_relocation_population']):,}", "Immediate decision-support priority"),
    ("Safe capacity", f"{available_capacity:,}", f"{coverage_pct:.0f}% of immediate demand"),
    ("Capacity gap", f"{capacity_gap:,}", "Uncovered immediate demand" if capacity_gap else "Current capacity covers immediate demand"),
])

st.markdown("## Incident picture")
left, right = st.columns([1.7, 1], gap="large")

with left:
    st.markdown(f"### {top['name']}")
    badge_col, score_col, population_col = st.columns([1, 1, 1.25], gap="small")
    with badge_col:
        render_risk_badge(top["risk_level"])
    with score_col:
        st.metric("Risk", f"{float(top['risk_score']):.1f}/100")
    with population_col:
        st.metric("Population", f"{int(top['population']):,}")

    st.write(f"**Primary risk drivers:** {top['risk_drivers']}")
    completeness = float(top.get("hazard_data_completeness", 0) or 0)
    st.progress(
        max(0.0, min(1.0, completeness / 100.0)),
        text=f"Hazard evidence completeness {completeness:.0f}%",
    )

    if str(top["risk_level"]).upper() == "CRITICAL":
        st.error(
            f"Highest-priority location is CRITICAL with {int(top['population']):,} people in scope. "
            "Review safe shelter capacity and route evidence before administrative action."
        )
    elif str(top["risk_level"]).upper() == "HIGH":
        st.warning("Highest-priority location is HIGH risk. Continue to relocation review and source validation.")
    else:
        st.info("No HIGH/CRITICAL location is currently at the top of this analytical scope.")

with right:
    if capacity_gap:
        render_source_card(
            "Capacity status",
            f"Gap: {capacity_gap:,}",
            "Available safe capacity is below immediate relocation demand. Multi-shelter planning or additional verified capacity is required.",
        )
    else:
        render_source_card(
            "Capacity status",
            "Covered",
            "Current safe available capacity is sufficient for the immediate relocation population in this analytical scope.",
        )
    st.markdown("### Next action")
    st.page_link("pages/2_Red_Zone_Map.py", label="1 · Inspect hazard map", use_container_width=True)
    st.page_link("pages/3_Risk_Analysis.py", label="2 · Explain the risk", use_container_width=True)
    st.page_link("pages/4_Relocation_Planner.py", label="3 · Build relocation plan", use_container_width=True)
    st.page_link("pages/0_Operations_Hub.py", label="4 · Check live context", use_container_width=True)

st.markdown("## Priority queue")
queue_cols = [
    c
    for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"]
    if c in priority.columns
]
queue = priority[queue_cols].head(8).copy()
st.dataframe(
    queue,
    width="stretch",
    hide_index=True,
    column_config={
        "risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%.1f"),
        "population": st.column_config.NumberColumn("Population", format=",%d"),
    },
)

st.markdown("## Risk distribution")
levels = ["CRITICAL", "HIGH", "MODERATE", "LOW"]
counts = {level: int((priority["risk_level"] == level).sum()) for level in levels}
population_by_level = {
    level: int(priority.loc[priority["risk_level"] == level, "population"].sum())
    for level in levels
}
columns = st.columns(4, gap="small")
for column, level in zip(columns, levels):
    with column:
        color = RISK_COLORS[level]
        st.markdown(
            f"<div class='hz-card' style='border-top:3px solid {color}'>"
            f"<div class='label'>{level}</div>"
            f"<div class='value'>{counts[level]} locations</div>"
            f"<div class='detail'>{population_by_level[level]:,} people</div>"
            "</div>",
            unsafe_allow_html=True,
        )

st.markdown("## Operator workspace")
workflow_left, workflow_mid, workflow_right = st.columns(3, gap="large")
with workflow_left:
    render_source_card(
        "Hazard & exposure",
        "Map-first review",
        "Inspect red zones, affected population, qualified shelters and route provenance in one spatial view.",
    )
    st.page_link("pages/2_Red_Zone_Map.py", label="Open map →")
with workflow_mid:
    render_source_card(
        "Relocation decision",
        "Capacity constrained",
        "Rank only shelters that pass safety and available-capacity gates; never overallocate shared resources.",
    )
    st.page_link("pages/4_Relocation_Planner.py", label="Open planner →")
with workflow_right:
    render_source_card(
        "Situation context",
        "Source aware",
        "Refresh external context when connected while keeping uncalibrated observations separate from baseline analytical risk.",
    )
    st.page_link("pages/0_Operations_Hub.py", label="Open context →")

with st.expander("Evidence, assumptions & system tools", expanded=False):
    tool_cols = st.columns(4, gap="small")
    links = [
        ("Operational data", "pages/9_Operational_Data.py"),
        ("System readiness", "pages/8_System_Readiness.py"),
        ("GIS evidence", "pages/10_GIS_Source_Inspector.py"),
        ("Method", "pages/6_Methodology.py"),
    ]
    for col, (label, path) in zip(tool_cols, links):
        with col:
            st.page_link(path, label=label, use_container_width=True)

render_disclaimer()
