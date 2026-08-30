import streamlit as st

from src.pipeline import (
    calculate_summary,
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
)
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(
    page_title="Multi-Hazard Decision Support System",
    page_icon="MH",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_css()

render_page_header(
    "Multi-Hazard Decision Support System",
    "Emergency Operations Centre | SIH26191 | Situation awareness, risk prioritization and relocation planning",
)
render_data_mode_indicator("DEMO")

try:
    habitations_raw, shelters_raw = load_demo_data()
    try:
        hazards = load_demo_hazards()
    except Exception:
        hazards = None

    habitations = enrich_habitations(habitations_raw, hazard_data=hazards)
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
except Exception:
    st.error(
        "The demonstration data could not be loaded. Confirm that the files in data/demo/ "
        "are present and match the frozen data contracts."
    )
    render_disclaimer()
    st.stop()

render_kpi_strip(
    [
        ("Habitations Monitored", f"{summary['habitations_monitored']:,}", None),
        ("Critical Red Zones", f"{summary['critical_red_zones']:,}", None),
        ("Population at Risk", f"{summary['population_at_risk']:,}", "HIGH + CRITICAL habitations"),
        ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", "Population in IMMEDIATE-priority habitations"),
        ("Available Shelter Capacity", f"{int(summary['available_shelter_capacity']):,}", "Capacity after limiting-resource constraints"),
    ]
)

st.divider()

left, right = st.columns([1.35, 1], gap="large")
with left:
    st.subheader("Current Risk Situation")
    top = habitations.sort_values("risk_score", ascending=False).iloc[0]
    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(f"### {top['name']}")
        st.caption(f"Highest current demonstration risk score: {top['risk_score']:.1f}/100")
        st.write(
            f"Population exposed: **{int(top['population']):,}**  |  "
            f"Relocation priority: **{top['relocation_priority']}**"
        )
        st.write(f"Primary risk drivers: **{top['risk_drivers']}**")
        if top.get("inside_hazard_zone") is not None:
            location_status = "Inside demonstration hazard polygon" if top["inside_hazard_zone"] else "Outside demonstration hazard polygon"
            st.caption(location_status)
    with c2:
        render_risk_badge(top["risk_level"])

    st.markdown("#### Highest-risk habitations")
    display = habitations[
        ["name", "population", "risk_score", "risk_level", "relocation_priority"]
    ].sort_values("risk_score", ascending=False)
    st.dataframe(
        display.head(10),
        width="stretch",
        hide_index=True,
        column_config={
            "name": "Habitation",
            "population": st.column_config.NumberColumn("Population", format="%d"),
            "risk_score": st.column_config.NumberColumn("Risk Score", format="%.1f"),
            "risk_level": "Risk Level",
            "relocation_priority": "Relocation Priority",
        },
    )

with right:
    st.subheader("Priority Actions")
    st.markdown(
        """
        1. **Review Red Zones** — identify the most exposed habitations on the map.
        2. **Inspect Risk Drivers** — confirm why each habitation is classified as high or critical.
        3. **Plan Relocation** — compare safe shelters, capacity and route distance.
        4. **Test Scenarios** — adjust risk weights and measure classification impact.
        5. **Export a Draft Action Plan** — use the result as administrative decision support.
        """
    )

    st.markdown("#### System status")
    st.success("Offline demonstration pipeline is available.")
    if hazards is not None:
        st.success("Synthetic GIS hazard polygons loaded for pipeline testing.")
    else:
        st.warning("GIS hazard layer unavailable; stored demonstration hazard scores are being used.")
    st.info(
        "Live IMD / NDMA / CWC adapters are intentionally separate. Until connected and verified, "
        "the application must continue to display DEMONSTRATION DATA."
    )

st.divider()
st.subheader("Operational Modules")
modules = st.columns(5)
module_text = [
    ("Command Center", "Monitor risk, population exposure and shelter capacity."),
    ("Red Zone Map", "View habitation locations and risk classes spatially."),
    ("Risk Analysis", "Inspect factor contributions and relocation priority."),
    ("Relocation Planner", "Compare capacity-aware shelter recommendations."),
    ("Scenario Studio", "Adjust risk weights and measure scenario impact."),
]
for col, (name, description) in zip(modules, module_text):
    with col:
        st.markdown(f"**{name}**")
        st.caption(description)

render_disclaimer()
