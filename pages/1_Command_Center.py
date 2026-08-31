import pandas as pd
import plotly.express as px
import streamlit as st

from src.earthquake_context import fetch_recent_earthquakes
from src.live_alerts import fetch_disaster_alerts
from src.pipeline import (
    calculate_summary,
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
    load_uploaded_habitations,
    load_uploaded_shelters,
)
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_upload_controls,
)

st.set_page_config(page_title="Command Center", layout="wide")
inject_global_css()
render_page_header("Command Center", "Operational summary of multi-hazard risk, exposed population, warnings and shelter capacity.")
render_data_mode_indicator("DEMO")
city, hazard_profile = render_demo_scope_controls("command")
uploaded_habitations, uploaded_shelters = render_upload_controls("command")

try:
    habitations_raw, shelters_raw = load_demo_data(city)
    if uploaded_habitations is not None:
        habitations_raw = load_uploaded_habitations(uploaded_habitations)
        st.sidebar.warning("Habitation CSV is user supplied and is not treated as LIVE government data.")
    if uploaded_shelters is not None:
        shelters_raw = load_uploaded_shelters(uploaded_shelters)
        st.sidebar.warning("Shelter CSV is user supplied and is not treated as LIVE government data.")
    try:
        hazards = load_demo_hazards()
    except Exception:
        hazards = None
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type=hazard_profile)
    shelters = enrich_shelters(shelters_raw)
except Exception as exc:
    st.error(f"Unable to prepare the command-center dataset: {exc}")
    render_disclaimer()
    st.stop()

with st.sidebar:
    st.subheader("Filters")
    district_options = ["All"] + sorted(habitations["district_code"].dropna().astype(str).unique().tolist()) if "district_code" in habitations.columns else ["All"]
    district = st.selectbox("District", district_options)
    risk_filter = st.selectbox("Risk level", ["All", "CRITICAL", "HIGH", "MODERATE", "LOW"])

filtered = habitations.copy()
if district != "All" and "district_code" in filtered.columns:
    filtered = filtered[filtered["district_code"].astype(str) == district]
if risk_filter != "All":
    filtered = filtered[filtered["risk_level"] == risk_filter]

summary = calculate_summary(filtered, shelters)
render_kpi_strip([
    ("Habitations", f"{summary['habitations_monitored']:,}", None),
    ("Critical", f"{summary['critical_red_zones']:,}", None),
    ("Population at Risk", f"{summary['population_at_risk']:,}", None),
    ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", None),
    ("Shelter Capacity", f"{int(summary['available_shelter_capacity']):,}", "Available after limiting-resource constraints"),
])
st.caption(f"Active hazard profile: **{hazard_profile.title()}** · Prototype hazard-model completeness is shown per location.")

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["Risk Overview", "Habitation Data", "Shelter Capacity", "External Context"])
with tab1:
    left, right = st.columns(2, gap="large")
    with left:
        counts = filtered["risk_level"].value_counts().reindex(["CRITICAL", "HIGH", "MODERATE", "LOW"], fill_value=0).rename_axis("Risk Level").reset_index(name="Habitations")
        st.plotly_chart(px.bar(counts, x="Risk Level", y="Habitations", title="Habitations by Risk Class"), width="stretch")
    with right:
        priority = filtered["relocation_priority"].value_counts().reindex(["IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM", "MONITOR"], fill_value=0).rename_axis("Priority").reset_index(name="Habitations")
        st.plotly_chart(px.bar(priority, x="Priority", y="Habitations", title="Relocation Priority"), width="stretch")
    table_columns = [c for c in ["name", "demo_city", "population", "risk_score", "risk_level", "relocation_priority", "coordination_zone", "hazard_data_completeness", "risk_drivers"] if c in filtered.columns]
    st.subheader("Highest-risk locations")
    st.dataframe(filtered[table_columns].sort_values("risk_score", ascending=False), width="stretch", hide_index=True)

with tab2:
    st.dataframe(filtered.sort_values("risk_score", ascending=False), width="stretch", hide_index=True)
    template = "habitation_id,name,latitude,longitude,population,children_population,elderly_population,exposure_score,accessibility_score,hazard_score\nEXAMPLE,Example Location,20.0,85.0,1000,180,90,70,60,50\n"
    st.download_button("Download minimum habitation CSV template", template, "habitation_template.csv", "text/csv")

with tab3:
    total_available = shelters["available_capacity"].sum()
    total_effective = shelters["effective_capacity"].sum()
    total_occupied = shelters["current_occupancy"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Effective Capacity", f"{int(total_effective):,}")
    c2.metric("Current Occupancy", f"{int(total_occupied):,}")
    c3.metric("Available Capacity", f"{int(total_available):,}")
    columns = [c for c in ["name", "demo_city", "effective_capacity", "current_occupancy", "available_capacity", "capacity_validation_status", "safety_score"] if c in shelters.columns]
    st.dataframe(shelters[columns].sort_values("available_capacity", ascending=False), width="stretch", hide_index=True)

with tab4:
    alert_tab, earthquake_tab = st.tabs(["NDMA SACHET-compatible Alerts", "USGS Earthquake Context"])
    with alert_tab:
        st.caption("The official SACHET portal uses CAP-based alert dissemination. This connector is labelled LIVE only when a verified feed URL is explicitly configured; otherwise it uses cached or DEMO content.")
        alert_result = fetch_disaster_alerts()
        render_data_mode_indicator(alert_result["mode"])
        st.caption(f"Source: {alert_result['source']} | Retrieved: {alert_result['fetched_at']}")
        if alert_result.get("stale"):
            st.warning("Displayed alert data is cached because the source could not be refreshed.")
        if alert_result.get("error"):
            st.warning("Configured alert source was unavailable; demonstration alerts are shown instead.")
        alerts = pd.DataFrame(alert_result.get("alerts", []))
        if alerts.empty:
            st.info("No alerts were returned by the configured feed.")
        else:
            display_columns = [c for c in ["event", "severity", "urgency", "area", "headline", "published"] if c in alerts.columns]
            st.dataframe(alerts[display_columns], width="stretch", hide_index=True)
        st.info("Do not invent a SACHET identifier or mark an unverified endpoint LIVE. External alerts remain separate from the deterministic risk score unless a verified source-specific mapping is implemented.")

    with earthquake_tab:
        context_city = city if city in {"Puri", "Guwahati", "Chennai"} else st.selectbox("Context city", ["Guwahati", "Puri", "Chennai"], key="earthquake_context_city")
        st.caption("Optional official USGS FDSN earthquake-catalog context. This external feed does not silently alter the project's risk score or replace Indian seismic-hazard products.")
        try:
            earthquake_result = fetch_recent_earthquakes(context_city)
            render_data_mode_indicator(earthquake_result["mode"])
            st.caption(f"Source: {earthquake_result['source']} | Retrieved: {earthquake_result['fetched_at']}")
            if earthquake_result.get("stale"):
                st.warning("USGS context is being shown from cache because the source could not be refreshed.")
            quake_df = pd.DataFrame(earthquake_result.get("events", []))
            if quake_df.empty:
                st.info("No matching earthquakes were returned for the selected search window and radius.")
            else:
                show = [c for c in ["magnitude", "place", "depth_km", "time", "latitude", "longitude"] if c in quake_df.columns]
                st.dataframe(quake_df[show].head(25), width="stretch", hide_index=True)
        except Exception as exc:
            st.info(f"USGS earthquake context is unavailable right now; the offline DEMO analysis continues normally. ({exc})")

render_disclaimer()
