from __future__ import annotations

import pandas as pd
import streamlit as st

from src.live_operations import fetch_operations_snapshot
from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
    render_source_card,
)

st.set_page_config(page_title="Operations Hub", page_icon="EOC", layout="wide", initial_sidebar_state="expanded")
inject_global_css()
render_page_header(
    "Operations Hub",
    "Real-time situational awareness + explainable relocation planning for SIH26191. External context is source-labelled and never silently changes the baseline risk model.",
)

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds could not be activated automatically: {exc}")

operational_payload = resolved["payload"] if resolved else None
with st.sidebar:
    st.subheader("Incident scope")
    if resolved:
        scope_label = operational_payload.get("label", "Operational dataset")
        st.success(f"Operational workspace: {scope_label}")
        if resolved.get("origin") == "configured_feeds":
            st.caption("Loaded from configured HTTPS feeds · server cache 5 min")
        hazard_profile = st.selectbox(
            "Analytical hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: value.replace("_", " ").title(),
        )
        st.page_link("pages/9_Operational_Data.py", label="Manage Operational Data", use_container_width=True)
    else:
        city = st.selectbox("Fallback study geography", ["Puri", "Guwahati", "Chennai"], index=0)
        scope_label = city
        hazard_profile = st.selectbox(
            "Analytical hazard profile",
            ["combined", "flood", "cyclone", "landslide", "earthquake", "drought", "stored"],
            index=0,
            format_func=lambda value: value.replace("_", " ").title(),
        )
        st.caption("Load real datasets in Operational Data to replace this fallback scope.")
    st.subheader("Live context")
    days = st.slider("Look-back window", 1, 30, 7)
    radius_km = st.slider("Event radius (km)", 100, 1000, 500, 50)
    min_magnitude = st.slider("Minimum earthquake magnitude", 0.0, 6.0, 2.5, 0.5)
    refresh_live = st.button("Refresh live sources", type="primary", width="stretch")
    st.caption("Refresh is operator-controlled and independent sources are fetched concurrently for lower latency.")

try:
    if resolved:
        habitations_raw = resolved["habitations"]
        shelters_raw = resolved["shelters"]
    else:
        habitations_raw, shelters_raw = load_demo_data(city)
    habitations = enrich_habitations(
        habitations_raw,
        hazard_data=None,
        hazard_type=hazard_profile,
        add_coordination_zones=False,
    )
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
except Exception as exc:
    st.error(f"Unable to prepare deterministic operations data: {exc}")
    render_disclaimer()
    st.stop()

nav = st.columns(6, gap="small")
links = [
    ("Operational Data", "pages/9_Operational_Data.py"),
    ("Red Zone Map", "pages/2_Red_Zone_Map.py"),
    ("Risk Analysis", "pages/3_Risk_Analysis.py"),
    ("Relocation", "pages/4_Relocation_Planner.py"),
    ("Live Explorer", "pages/7_Live_Data_Context.py"),
    ("Readiness", "pages/8_System_Readiness.py"),
]
for column, (label, page) in zip(nav, links):
    with column:
        st.page_link(page, label=label, use_container_width=True)

scope_kind = "operational" if operational_payload else "fallback DEMO"
st.caption(
    f"Active {scope_kind} scope: **{scope_label}** · **{hazard_profile.title()}** · baseline deterministic risk remains independent from uncalibrated live feeds."
)

render_kpi_strip([
    ("Habitations", f"{summary['habitations_monitored']:,}", "Current analytical scope"),
    ("Critical", f"{summary['critical_red_zones']:,}", "Critical analytical red zones"),
    ("Population at Risk", f"{summary['population_at_risk']:,}", "HIGH + CRITICAL"),
    ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", "Priority population"),
    ("Available Capacity", f"{int(summary['available_shelter_capacity']):,}", "After limiting-resource constraints"),
])

st.markdown("## Incident decision picture")
left, middle, right = st.columns([1.35, 1, 1], gap="large")

top = habitations.sort_values("risk_score", ascending=False).iloc[0]
with left:
    st.markdown(f"### {top['name']}")
    render_risk_badge(top["risk_level"])
    st.metric("Explainable Risk Score", f"{float(top['risk_score']):.1f} / 100")
    st.write(f"**Relocation priority:** {top['relocation_priority']}")
    st.write(f"**Population:** {int(top['population']):,}")
    st.write(f"**Risk drivers:** {top['risk_drivers']}")
    st.caption("This remains decision support. The system does not issue an evacuation order.")
with middle:
    render_source_card(
        "Capacity gate",
        f"{int(summary['available_shelter_capacity']):,} available",
        "Safety and limiting-resource capacity are hard constraints before shelter ranking or optimization.",
    )
    st.metric("Safe inventory records", len(shelters[shelters.get("safety_score", 100) >= 50]) if "safety_score" in shelters.columns else len(shelters))
with right:
    render_source_card(
        "Analytical model",
        "Explainable / deterministic",
        "Risk = 0.35H + 0.25E + 0.25V + 0.15A. External context remains isolated until calibrated.",
    )
    st.metric("Hazard completeness", f"{float(top.get('hazard_data_completeness', 0)):.0f}%")

st.markdown("### Highest-priority habitations")
cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"] if c in habitations.columns]
st.dataframe(habitations[cols].sort_values("risk_score", ascending=False), width="stretch", hide_index=True)

st.divider()
st.markdown("## Real-time source console")

if operational_payload:
    center = operational_payload["center"]
    live_kwargs = {
        "latitude": float(center["latitude"]),
        "longitude": float(center["longitude"]),
        "days": days,
        "radius_km": radius_km,
        "min_magnitude": min_magnitude,
    }
else:
    live_kwargs = {"days": days, "radius_km": radius_km, "min_magnitude": min_magnitude}

snapshot_key = f"operations_snapshot_{scope_label}_{days}_{radius_km}_{min_magnitude}"
if refresh_live:
    with st.spinner("Refreshing weather, air quality, earthquake, disaster-event and official-source context in parallel..."):
        st.session_state[snapshot_key] = fetch_operations_snapshot(scope_label, **live_kwargs)

snapshot = st.session_state.get(snapshot_key)
if snapshot is None:
    st.info("Click **Refresh live sources** to load the real-time situational layer. The deterministic relocation workflow above is already available offline.")
else:
    sources = snapshot["sources"]
    weather = sources["weather"]
    air = sources["air_quality"]
    current_weather = weather.get("current", {}) or {}
    current_air = air.get("current", {}) or {}
    weather_units = weather.get("current_units", {}) or {}
    air_units = air.get("current_units", {}) or {}

    status_cols = st.columns(7, gap="small")
    health_lookup = {row["source"]: row for row in snapshot["source_health"]}
    for column, key, label in [
        (status_cols[0], "weather", "Weather"),
        (status_cols[1], "air_quality", "Air"),
        (status_cols[2], "usgs", "USGS"),
        (status_cols[3], "gdacs", "GDACS"),
        (status_cols[4], "eonet", "EONET"),
        (status_cols[5], "imd", "IMD"),
        (status_cols[6], "sachet", "SACHET"),
    ]:
        with column:
            st.markdown(f"**{label}**")
            render_data_mode_indicator(health_lookup[key]["mode"])
            if health_lookup[key].get("stale"):
                st.caption("STALE CACHE")

    live_metrics = st.columns(6, gap="small")
    temperature = current_weather.get("temperature_2m")
    precipitation = current_weather.get("precipitation")
    wind = current_weather.get("wind_speed_10m")
    aqi = current_air.get("us_aqi")
    pm25 = current_air.get("pm2_5")
    live_metrics[0].metric("Temperature", f"{temperature} {weather_units.get('temperature_2m', '')}" if temperature is not None else "—")
    live_metrics[1].metric("Precipitation", f"{precipitation} {weather_units.get('precipitation', '')}" if precipitation is not None else "—")
    live_metrics[2].metric("Wind", f"{wind} {weather_units.get('wind_speed_10m', '')}" if wind is not None else "—")
    live_metrics[3].metric("US AQI", aqi if aqi is not None else "—")
    live_metrics[4].metric("PM2.5", f"{pm25} {air_units.get('pm2_5', '')}" if pm25 is not None else "—")
    live_metrics[5].metric("Nearby Events", len(snapshot["events"]))

    event_col, health_col = st.columns([1.45, 1], gap="large")
    with event_col:
        st.markdown("### Nearby event register")
        events = pd.DataFrame(snapshot["events"])
        if events.empty:
            st.success("No matching nearby event was returned for the selected time/radius window.")
        else:
            event_columns = [c for c in ["source", "type", "event", "magnitude", "distance_km", "time", "url"] if c in events.columns]
            st.dataframe(events[event_columns].head(50), width="stretch", hide_index=True)
            safe_name = "operational" if operational_payload else str(scope_label).lower().replace(" ", "_")
            st.download_button(
                "Download live event register",
                data=events.to_csv(index=False).encode("utf-8"),
                file_name=f"{safe_name}_operations_events.csv",
                mime="text/csv",
                width="stretch",
            )
    with health_col:
        st.markdown("### Source diagnostics")
        diagnostics = pd.DataFrame(snapshot["source_health"])
        if not diagnostics.empty:
            diagnostics = diagnostics.astype(str)
            st.dataframe(diagnostics, width="stretch", hide_index=True)
        st.caption(f"Snapshot generated: {snapshot['generated_at']}")
        st.warning("Live observations are corroborating evidence only until a verified source-specific calibration is approved for analytical scoring.")

st.divider()
st.markdown("## Operator workflow")
workflow = st.columns(5, gap="small")
steps = [
    ("01", "Detect", "Refresh source context and inspect current conditions."),
    ("02", "Prioritize", "Use explainable risk and relocation priority."),
    ("03", "Validate", "Reject unsafe/full sites and inspect capacity evidence."),
    ("04", "Move", "Select a safe candidate and verify route provenance."),
    ("05", "Brief", "Export a reviewable draft action plan with assumptions."),
]
for column, (number, title, text) in zip(workflow, steps):
    with column:
        render_source_card(f"{number} · {title}", "EOC step", text)

render_disclaimer()
