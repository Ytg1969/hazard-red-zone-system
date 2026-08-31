import streamlit as st

from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
    render_source_card,
)

st.set_page_config(page_title="Multi-Hazard Decision Support System", page_icon="MH", layout="wide", initial_sidebar_state="expanded")
inject_global_css()
render_page_header(
    "Multi-Hazard Decision Support System",
    "Emergency Operations Centre | SIH26191 | Situation awareness, explainable risk and capacity-aware relocation planning",
)
render_data_mode_indicator("DEMO")
city, hazard_profile = render_demo_scope_controls("overview")

try:
    habitations_raw, shelters_raw = load_demo_data(city)
    try:
        hazards = load_demo_hazards()
    except Exception:
        hazards = None
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type=hazard_profile)
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
except Exception as exc:
    st.error(f"The demonstration data could not be prepared: {exc}")
    render_disclaimer()
    st.stop()

st.caption(f"Active geography: **{city}** · Hazard profile: **{hazard_profile.title()}** · Real geography with synthetic operational DEMO values")
render_kpi_strip([
    ("Habitations Monitored", f"{summary['habitations_monitored']:,}", None),
    ("Critical Red Zones", f"{summary['critical_red_zones']:,}", None),
    ("Population at Risk", f"{summary['population_at_risk']:,}", "HIGH + CRITICAL habitations"),
    ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", "Population in IMMEDIATE-priority habitations"),
    ("Available Shelter Capacity", f"{int(summary['available_shelter_capacity']):,}", "Capacity after limiting-resource constraints"),
])

st.divider()
left, right = st.columns([1.45, 1], gap="large")
with left:
    st.subheader("Current Risk Situation")
    top = habitations.sort_values("risk_score", ascending=False).iloc[0]
    c1, c2 = st.columns([2.4, 1])
    with c1:
        st.markdown(f"### {top['name']}")
        st.caption(f"Highest current demonstration risk score: {top['risk_score']:.1f}/100")
        st.write(f"Population exposed: **{int(top['population']):,}**  |  Relocation priority: **{top['relocation_priority']}**")
        st.write(f"Primary risk drivers: **{top['risk_drivers']}**")
        st.caption(f"Coordination grouping: {top.get('coordination_zone', '—')} · Hazard data completeness: {float(top.get('hazard_data_completeness', 0)):.0f}%")
    with c2:
        render_risk_badge(top["risk_level"])
        st.metric("Risk", f"{top['risk_score']:.1f}")

    st.markdown("#### Highest-risk habitations")
    display_cols = ["name", "demo_city", "population", "risk_score", "risk_level", "relocation_priority", "coordination_zone"]
    display_cols = [c for c in display_cols if c in habitations.columns]
    st.dataframe(habitations[display_cols].sort_values("risk_score", ascending=False).head(10), width="stretch", hide_index=True)

with right:
    st.subheader("Operator Next Actions")
    st.info("Use this sequence during a live briefing. Each module preserves the same city and hazard logic, while live sources remain analytically isolated unless explicitly calibrated.")
    st.markdown(
        """
        **01 — Scope the incident**  
        Choose the geography and active hazard profile.

        **02 — Verify the red zones**  
        Open the map, compare synthetic footprints with source GIS context, and inspect the highest-risk habitation.

        **03 — Explain the score**  
        Review hazard, exposure, vulnerability and evacuation-difficulty contributions.

        **04 — Plan movement**  
        Filter unsafe/full shelters, allocate capacity, inspect the route and preserve any deficit.

        **05 — Export the brief**  
        Generate the draft Markdown/PDF action plan for administrative review.
        """
    )
    st.success("Core deterministic workflow is offline-ready.")
    st.caption("Puri, Guwahati and Chennai are representative high-risk contexts, not a definitive national ranking.")

st.divider()
st.subheader("Data & Decision Layers")
source_cols = st.columns(3, gap="large")
with source_cols[0]:
    render_source_card("Deterministic analysis", "Offline-ready", "Risk, capacity, relocation and exports continue without internet access.")
with source_cols[1]:
    render_source_card("Verified live context", "Weather · Quakes · Events", "Open-Meteo, USGS and GDACS are source-labelled and kept separate from scoring unless calibrated.")
with source_cols[2]:
    render_source_card("Authoritative GIS context", "NRSC / ISRO Bhuvan", "Verified WMS overlays can be shown beside DEMO hazard footprints without silently changing the score.")

st.divider()
st.subheader("Operational Modules")
module_text = [
    ("Command Center", "Monitor incident context, exposure, alerts and capacity status."),
    ("Red Zone Map", "Inspect risk, Bhuvan context, shelter destination and evacuation route."),
    ("Risk Analysis", "See exactly which weighted components drive the final risk score."),
    ("Relocation Planner", "Rank safe shelters, split population and protect shared capacity."),
    ("Scenario Studio", "Test policy-weight changes without changing the frozen production contract."),
    ("Live Data Context", "Refresh real-world sources and see LIVE/CACHED/DEMO provenance clearly."),
]
for start in range(0, len(module_text), 3):
    row = st.columns(3, gap="large")
    for col, (name, description) in zip(row, module_text[start:start + 3]):
        with col:
            render_source_card(name, "Open module", description)

render_disclaimer()
