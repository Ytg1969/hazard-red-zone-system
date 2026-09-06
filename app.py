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

st.set_page_config(
    page_title="Hazard Command",
    page_icon="HZ",
    layout="wide",
    initial_sidebar_state="auto",
)
inject_global_css()
render_page_header(
    "Hazard Command",
    "A focused operations workspace for identifying red zones, explaining risk and planning safe relocation under capacity constraints.",
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
        st.markdown("### Active scope")
        st.success(active_label)
        hazard_profile = st.selectbox(
            "Hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: value.replace("_", " ").title(),
            key="overview_operational_hazard",
        )
    if active_mode in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(active_mode)
    else:
        st.warning("Active workspace provenance is unverified.")
    context_caption = f"{active_label} · {hazard_profile.replace('_', ' ').title()}"
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("overview")
    habitations_raw, shelters_raw = load_demo_data(city)
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

st.caption(context_caption)
render_kpi_strip([
    ("Locations", f"{summary['habitations_monitored']:,}", None),
    ("Critical red zones", f"{summary['critical_red_zones']:,}", None),
    ("Population at risk", f"{summary['population_at_risk']:,}", "HIGH + CRITICAL"),
    ("Immediate relocation", f"{summary['immediate_relocation_population']:,}", None),
    ("Available capacity", f"{int(summary['available_shelter_capacity']):,}", "After limiting-resource constraints"),
])

st.divider()
left, right = st.columns([1.7, 1], gap="large")

with left:
    st.subheader("Priority situation")
    top = habitations.sort_values("risk_score", ascending=False).iloc[0]
    c1, c2 = st.columns([2.4, 1])
    with c1:
        st.markdown(f"### {top['name']}")
        st.write(
            f"**{int(top['population']):,} people** exposed · "
            f"**{top['relocation_priority']}** relocation priority"
        )
        st.caption(f"Primary drivers: {top['risk_drivers']}")
        completeness = float(top.get("hazard_data_completeness", 0))
        st.progress(max(0.0, min(1.0, completeness / 100.0)), text=f"Hazard evidence completeness {completeness:.0f}%")
    with c2:
        render_risk_badge(top["risk_level"])
        st.metric("Risk score", f"{top['risk_score']:.1f}")

    table_cols = [
        c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority"]
        if c in habitations.columns
    ]
    st.dataframe(
        habitations[table_cols].sort_values("risk_score", ascending=False).head(8),
        width="stretch",
        hide_index=True,
    )

with right:
    st.subheader("Continue workflow")
    st.page_link("pages/0_Operations_Hub.py", label="Open Operations Hub", use_container_width=True)
    st.page_link("pages/2_Red_Zone_Map.py", label="Inspect Red Zone Map", use_container_width=True)
    st.page_link("pages/3_Risk_Analysis.py", label="Explain Risk Score", use_container_width=True)
    st.page_link("pages/4_Relocation_Planner.py", label="Plan Relocation", use_container_width=True)
    st.page_link("pages/9_Operational_Data.py", label="Manage Operational Data", use_container_width=True)

    st.markdown("#### Operating sequence")
    st.markdown(
        """
        1. Confirm the active geography and source mode.
        2. Inspect critical red zones and risk evidence.
        3. Review safe relocation capacity and route provenance.
        4. Export the action plan for administrative review.
        """
    )
    if resolved:
        st.success("Operational workspace active")
    else:
        st.info("Demo fallback active — load authority data before operational use.")

st.divider()
q1, q2, q3 = st.columns(3, gap="large")
with q1:
    st.markdown("### Red zones")
    st.caption("Map critical locations, hazard context, shelters and route evidence.")
    st.page_link("pages/2_Red_Zone_Map.py", label="Open map →")
with q2:
    st.markdown("### Relocation")
    st.caption("Rank safe shelters without overbooking shared capacity.")
    st.page_link("pages/4_Relocation_Planner.py", label="Open planner →")
with q3:
    st.markdown("### Live context")
    st.caption("Refresh weather, earthquake and disaster-event context when needed.")
    st.page_link("pages/7_Live_Data_Context.py", label="Open live context →")

render_disclaimer()
