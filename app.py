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
left, right = st.columns([1.35, 1], gap="large")
with left:
    st.subheader("Current Risk Situation")
    top = habitations.sort_values("risk_score", ascending=False).iloc[0]
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"### {top['name']}")
        st.caption(f"Highest current demonstration risk score: {top['risk_score']:.1f}/100")
        st.write(f"Population exposed: **{int(top['population']):,}**  |  Relocation priority: **{top['relocation_priority']}**")
        st.write(f"Primary risk drivers: **{top['risk_drivers']}**")
        st.caption(f"Coordination grouping: {top.get('coordination_zone', '—')} · Hazard data completeness: {float(top.get('hazard_data_completeness', 0)):.0f}%")
    with c2:
        render_risk_badge(top["risk_level"])

    st.markdown("#### Highest-risk habitations")
    display_cols = ["name", "demo_city", "population", "risk_score", "risk_level", "relocation_priority", "coordination_zone"]
    display_cols = [c for c in display_cols if c in habitations.columns]
    st.dataframe(habitations[display_cols].sort_values("risk_score", ascending=False).head(10), width="stretch", hide_index=True)

with right:
    st.subheader("Priority Actions")
    st.markdown(
        """
        1. **Choose hazard profile** — Flood, Cyclone, Landslide, Earthquake, Drought or Combined.
        2. **Review Red Zones** — identify the most exposed locations on the map.
        3. **Inspect Risk Drivers** — verify the weighted contribution behind every score.
        4. **Plan Relocation** — compare safe shelters, limiting capacity and route distance.
        5. **Test Scenarios** — adjust policy weights and compare impact.
        6. **Export Action Plan** — Markdown/PDF decision-support output.
        """
    )
    st.markdown("#### System status")
    st.success("Offline multi-city demonstration pipeline is available.")
    st.info("Puri, Guwahati and Chennai are representative high-risk contexts, not a definitive national ranking. See docs/multicity_demo_sources.md for source context and honesty rules.")

st.divider()
st.subheader("Operational Modules")
modules = st.columns(5)
module_text = [
    ("Command Center", "Monitor risk, population exposure, alerts and shelter capacity."),
    ("Red Zone Map", "View multi-city risk, hazard footprints and coordination zones."),
    ("Risk Analysis", "Inspect hazard-profile and final-risk contributions."),
    ("Relocation Planner", "Compare capacity-aware local shelter recommendations."),
    ("Scenario Studio", "Adjust risk weights and measure policy impact."),
]
for col, (name, description) in zip(modules, module_text):
    with col:
        st.markdown(f"**{name}**")
        st.caption(description)
render_disclaimer()
