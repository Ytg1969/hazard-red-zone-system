import pandas as pd
import plotly.express as px
import streamlit as st

from src.live_operations import fetch_operations_snapshot
from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_source_card,
)

st.set_page_config(page_title="Command Center", layout="wide")
inject_global_css()
render_page_header("Command Center", "Operational summary of multi-hazard risk, exposed population, source health and relocation capacity.")

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds are unavailable: {exc}")

if resolved:
    payload = resolved["payload"]
    habitations_raw = resolved["habitations"]
    shelters_raw = resolved["shelters"]
    active_label = str(payload.get("label", "Operational dataset"))
    mode = str(payload.get("habitation_mode", "UNVERIFIED"))
    center = payload.get("center", {})
    with st.sidebar:
        st.success(f"Operational workspace: {active_label}")
        hazard_profile = st.selectbox(
            "Analytical hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: value.title(),
            key="command_operational_hazard",
        )
        st.page_link("pages/9_Operational_Data.py", label="Manage Operational Data", use_container_width=True)
    if mode in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(mode)
    else:
        st.warning("Operational workspace provenance is UNVERIFIED.")
    data_caption = f"Operational geography: **{active_label}** · {hazard_profile.title()}"
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("command")
    habitations_raw, shelters_raw = load_demo_data(city)
    active_label = city
    center = {
        "latitude": float(habitations_raw["latitude"].mean()),
        "longitude": float(habitations_raw["longitude"].mean()),
    }
    data_caption = f"Fallback DEMO geography: **{city}** · {hazard_profile.title()}"

try:
    habitations = enrich_habitations(
        habitations_raw,
        hazard_data=None,
        hazard_type=hazard_profile,
        add_coordination_zones=False,
    )
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
st.caption(data_caption + " · live context remains analytically isolated until calibrated.")

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(["Risk Overview", "Habitation Data", "Shelter Capacity", "Live Source Console"])
with tab1:
    left, right = st.columns(2, gap="large")
    with left:
        counts = filtered["risk_level"].value_counts().reindex(["CRITICAL", "HIGH", "MODERATE", "LOW"], fill_value=0).rename_axis("Risk Level").reset_index(name="Habitations")
        st.plotly_chart(px.bar(counts, x="Risk Level", y="Habitations", title="Habitations by Risk Class"), width="stretch")
    with right:
        priority = filtered["relocation_priority"].value_counts().reindex(["IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM", "MONITOR"], fill_value=0).rename_axis("Priority").reset_index(name="Habitations")
        st.plotly_chart(px.bar(priority, x="Priority", y="Habitations", title="Relocation Priority"), width="stretch")
    table_columns = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "hazard_data_completeness", "risk_drivers"] if c in filtered.columns]
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
    columns = [c for c in ["name", "effective_capacity", "current_occupancy", "available_capacity", "capacity_validation_status", "safety_score"] if c in shelters.columns]
    st.dataframe(shelters[columns].sort_values("available_capacity", ascending=False), width="stretch", hide_index=True)

with tab4:
    st.caption("External sources are fetched only when requested. Independent feeds are queried concurrently to keep the page responsive.")
    cards = st.columns(4, gap="small")
    with cards[0]:
        render_source_card("Weather + AQI", "Open-Meteo", "Current weather and air quality at the operational-area center.")
    with cards[1]:
        render_source_card("Events", "USGS · GDACS · EONET", "Nearby earthquake and disaster-event context.")
    with cards[2]:
        render_source_card("IMD", "Approval dependent", "Official meteorological source; authorization failures remain visible.")
    with cards[3]:
        render_source_card("SACHET", "Configured CAP/RSS", "LIVE only after a verified feed is configured.")

    live_key = f"command_live_{active_label}_{float(center['latitude']):.4f}_{float(center['longitude']):.4f}"
    if st.button("Refresh operational live sources", type="primary", width="stretch"):
        with st.spinner("Refreshing independent live sources in parallel..."):
            st.session_state[live_key] = fetch_operations_snapshot(
                active_label,
                latitude=float(center["latitude"]),
                longitude=float(center["longitude"]),
                days=7,
                radius_km=300,
                min_magnitude=2.5,
            )

    snapshot = st.session_state.get(live_key)
    if not snapshot:
        st.info("No network request has been made on this page yet. Click refresh when current situational context is needed.")
    else:
        health = pd.DataFrame(snapshot.get("source_health", []))
        if not health.empty:
            health = health.astype(str)
            st.dataframe(health, width="stretch", hide_index=True)
        events = pd.DataFrame(snapshot.get("events", []))
        e1, e2 = st.columns([1.5, 1], gap="large")
        with e1:
            st.markdown("#### Nearby events")
            if events.empty:
                st.success("No matching nearby events were returned for the current search window.")
            else:
                event_columns = [c for c in ["source", "type", "event", "magnitude", "distance_km", "time", "url"] if c in events.columns]
                st.dataframe(events[event_columns].head(50), width="stretch", hide_index=True)
        with e2:
            sources = snapshot.get("sources", {})
            weather = sources.get("weather", {}).get("current", {}) or {}
            air = sources.get("air_quality", {}).get("current", {}) or {}
            st.metric("Temperature", weather.get("temperature_2m", "—"))
            st.metric("Precipitation", weather.get("precipitation", "—"))
            st.metric("Wind", weather.get("wind_speed_10m", "—"))
            st.metric("US AQI", air.get("us_aqi", "—"))
        st.warning("LIVE/CACHED observations are corroborating evidence only until source-specific calibration is approved for scoring.")

render_disclaimer()
