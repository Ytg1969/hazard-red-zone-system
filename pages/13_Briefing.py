from __future__ import annotations

import json
from datetime import datetime, timezone

import streamlit as st

from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(page_title="Incident Briefing", page_icon="BR", layout="wide", initial_sidebar_state="auto")
inject_global_css()
render_page_header(
    "Incident Briefing",
    "A compact administrative handoff built from the active analytical scope, with assumptions and provenance kept visible.",
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
    label = payload.get("label", "Operational dataset")
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
    if mode in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(mode)
    else:
        st.warning("Workspace provenance is unverified.")
else:
    render_data_mode_indicator("DEMO")
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
available_capacity = int(summary["available_shelter_capacity"])
immediate = int(summary["immediate_relocation_population"])
capacity_gap = max(0, immediate - available_capacity)

generated_at = datetime.now(timezone.utc).isoformat()

render_kpi_strip([
    ("People at risk", f"{int(summary['population_at_risk']):,}", "HIGH + CRITICAL"),
    ("Critical zones", f"{int(summary['critical_red_zones']):,}", "Analytical classification"),
    ("Immediate relocation", f"{immediate:,}", "Decision-support priority"),
    ("Available capacity", f"{available_capacity:,}", "Safety + limiting-resource constraints"),
    ("Capacity gap", f"{capacity_gap:,}", "Uncovered demand" if capacity_gap else "No current gap"),
])

left, right = st.columns([1.55, 1], gap="large")
with left:
    st.markdown("## Situation summary")
    st.markdown(f"### {top['name']}")
    render_risk_badge(top["risk_level"])
    st.write(
        f"Highest analytical risk is **{float(top['risk_score']):.1f}/100** for "
        f"**{int(top['population']):,} people**."
    )
    st.write(f"**Primary drivers:** {top['risk_drivers']}")
    st.write(f"**Relocation priority:** {top['relocation_priority']}")

    st.markdown("### Priority register")
    cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority"] if c in priority.columns]
    st.dataframe(priority[cols].head(8), width="stretch", hide_index=True)

with right:
    st.markdown("## Administrative status")
    if capacity_gap:
        st.error(f"Verified available capacity is short by **{capacity_gap:,} places** for immediate relocation demand.")
    else:
        st.success("Current verified available capacity covers immediate relocation demand in this analytical scope.")

    st.markdown("### Required review")
    st.markdown(
        "- Confirm active source mode and geography.\n"
        "- Validate highest-risk locations and risk evidence.\n"
        "- Confirm shelter safety, capacity and route provenance.\n"
        "- Treat this output as decision support for authorized officials."
    )

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

st.markdown("## Export")
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
