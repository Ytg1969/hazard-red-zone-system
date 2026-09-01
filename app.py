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
    render_source_card,
)

st.set_page_config(page_title="Multi-Hazard Decision Support System", page_icon="MH", layout="wide", initial_sidebar_state="expanded")
inject_global_css()
render_page_header(
    "Multi-Hazard Decision Support System",
    "Emergency Operations Centre | SIH26191 | Situation awareness, explainable risk and capacity-aware relocation planning",
)

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds could not be activated automatically: {exc}")

if resolved:
    operational_payload = resolved["payload"]
    habitations_raw = resolved["habitations"]
    shelters_raw = resolved["shelters"]
    active_label = operational_payload.get("label", "Operational dataset")
    active_mode = operational_payload.get("habitation_mode", "UNVERIFIED")
    with st.sidebar:
        st.success(f"Operational workspace: {active_label}")
        if resolved.get("origin") == "configured_feeds":
            st.caption("Loaded from configured HTTPS feeds · server cache 5 min")
        hazard_profile = st.selectbox(
            "Analytical hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: value.title(),
            key="overview_operational_hazard",
        )
        st.page_link("pages/9_Operational_Data.py", label="Manage Operational Data", use_container_width=True)
    if active_mode in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(active_mode)
    else:
        st.warning("Active operational data has unverified provenance.")
    context_caption = f"Active operational geography: **{active_label}** · Hazard profile: **{hazard_profile.title()}**"
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("overview")
    habitations_raw, shelters_raw = load_demo_data(city)
    operational_payload = None
    context_caption = f"Fallback geography: **{city}** · Hazard profile: **{hazard_profile.title()}** · synthetic operational DEMO values"

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
        st.caption(f"Highest current analytical risk score: {top['risk_score']:.1f}/100")
        st.write(f"Population exposed: **{int(top['population']):,}**  |  Relocation priority: **{top['relocation_priority']}**")
        st.write(f"Primary risk drivers: **{top['risk_drivers']}**")
        st.caption(f"Hazard data completeness: {float(top.get('hazard_data_completeness', 0)):.0f}%")
    with c2:
        render_risk_badge(top["risk_level"])
        st.metric("Risk", f"{top['risk_score']:.1f}")

    st.markdown("#### Highest-risk habitations")
    display_cols = ["name", "demo_city", "population", "risk_score", "risk_level", "relocation_priority"]
    display_cols = [c for c in display_cols if c in habitations.columns]
    st.dataframe(habitations[display_cols].sort_values("risk_score", ascending=False).head(10), width="stretch", hide_index=True)

with right:
    st.subheader("Operator Next Actions")
    if operational_payload:
        st.success("Operational data is active. Core analytical modules can use the same validated habitation and relocation-site workspace.")
    else:
        st.info("Fallback demo inputs are active. Open **Operational Data** to load authority/field datasets or configure HTTPS feeds.")
    st.markdown(
        """
        **01 — Scope the incident**  
        Choose the operational geography and active hazard profile.

        **02 — Verify the red zones**  
        Inspect GIS evidence and the highest-risk habitation.

        **03 — Explain the score**  
        Review hazard, exposure, vulnerability and evacuation-difficulty contributions.

        **04 — Plan movement**  
        Filter unsafe/full shelters, allocate capacity, inspect the route and preserve any deficit.

        **05 — Export the brief**  
        Generate the draft Markdown/PDF action plan for administrative review.
        """
    )
    st.success("Core deterministic workflow remains offline-ready.")

st.divider()
st.subheader("Data & Decision Layers")
source_cols = st.columns(3, gap="large")
with source_cols[0]:
    render_source_card("Operational workspace", "Upload or HTTPS feed", "Validated authority/field datasets can replace bundled habitation and shelter inputs without changing safety contracts.")
with source_cols[1]:
    render_source_card("Verified live context", "Weather · Quakes · Events", "Open-Meteo, USGS, GDACS and EONET are source-labelled and kept separate from scoring unless calibrated.")
with source_cols[2]:
    render_source_card("Authoritative GIS context", "NRSC / ISRO Bhuvan", "Verified WMS overlays can be shown beside analytical hazard evidence without silently changing the score.")

st.divider()
st.subheader("Operational Modules")
module_text = [
    ("Operational Data", "Load real habitation/shelter datasets or configured HTTPS feeds."),
    ("Operations Hub", "Refresh live context on demand while deterministic planning stays available offline."),
    ("Red Zone Map", "Inspect risk, Bhuvan context, shelter destination and evacuation route."),
    ("Risk Analysis", "See exactly which weighted components drive the final risk score."),
    ("Relocation Planner", "Rank safe shelters, split population and protect shared capacity."),
    ("System Readiness", "Inspect source health, provenance and candidate production datasets."),
]
for start in range(0, len(module_text), 3):
    row = st.columns(3, gap="large")
    for col, (name, description) in zip(row, module_text[start:start + 3]):
        with col:
            render_source_card(name, "Open module", description)

render_disclaimer()
