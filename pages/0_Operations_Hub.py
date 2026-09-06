from __future__ import annotations

import pandas as pd
import streamlit as st

from src.live_operations import fetch_operations_snapshot
from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters, load_demo_data
from src.runtime_mode import offline_mode
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

st.set_page_config(page_title="Operations Hub", page_icon="EOC", layout="wide", initial_sidebar_state="auto")
inject_global_css()
render_page_header(
    "Operations Hub",
    "Situational awareness + explainable relocation planning. External context is source-labelled and never silently changes the baseline risk model.",
)

is_offline = offline_mode()
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
    with st.expander("Source context controls", expanded=False):
        days = st.slider("Look-back window", 1, 30, 7)
        radius_km = st.slider("Event radius (km)", 100, 1000, 500, 50)
        min_magnitude = st.slider("Minimum earthquake magnitude", 0.0, 6.0, 2.5, 0.5)
    refresh_label = "Show offline source state" if is_offline else "Refresh live sources"
    refresh_live = st.button(refresh_label, type="primary", width="stretch")
    if is_offline:
        st.caption("Offline field mode is active. Refresh records source unavailability without making network calls.")
    else:
        st.caption("Refresh is operator-controlled; live context remains separate from baseline risk.")

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
top = habitations.sort_values("risk_score", ascending=False).iloc[0]
safe_inventory = len(shelters[shelters.get("safety_score", 100) >= 50]) if "safety_score" in shelters.columns else len(shelters)
render_risk_badge(top["risk_level"])
render_kpi_strip([
    ("Highest Risk", f"{float(top['risk_score']):.1f}/100", str(top["name"])),
    ("Population", f"{int(top['population']):,}", "Highest-priority habitation"),
    ("Relocation Priority", top["relocation_priority"], "Decision-support priority"),
    ("Safe Inventory", safe_inventory, "Records meeting safety threshold"),
    ("Hazard Completeness", f"{float(top.get('hazard_data_completeness', 0)):.0f}%", "Evidence completeness"),
])
st.write(f"**Risk drivers:** {top['risk_drivers']}")
st.caption("This remains decision support. The system does not issue an evacuation order.")

picture_left, picture_right = st.columns(2, gap="large")
with picture_left:
    render_source_card(
        "Capacity gate",
        f"{int(summary['available_shelter_capacity']):,} available",
        "Safety and limiting-resource capacity are hard constraints before shelter ranking or optimization.",
    )
with picture_right:
    render_source_card(
        "Analytical model",
        "Explainable / deterministic",
        "Risk = 0.35H + 0.25E + 0.25V + 0.15A. External context remains isolated until calibrated.",
    )

priority_rows = habitations.sort_values("risk_score", ascending=False)
st.markdown("### Highest-priority habitations")
cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"] if c in habitations.columns]
st.dataframe(priority_rows[cols].head(10), width="stretch", hide_index=True)
if len(priority_rows) > 10:
    with st.expander(f"Full priority register · {len(priority_rows)} records", expanded=False):
        st.dataframe(priority_rows[cols], width="stretch", hide_index=True)

st.divider()
st.markdown("## Source console")

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

snapshot_key = f"operations_snapshot_{scope_label}_{days}_{radius_km}_{min_magnitude}_{'offline' if is_offline else 'connected'}"
if refresh_live:
    spinner_text = "Recording offline source state..." if is_offline else "Refreshing weather, air quality, earthquake, disaster-event and official-source context in parallel..."
    with st.spinner(spinner_text):
        st.session_state[snapshot_key] = fetch_operations_snapshot(scope_label, **live_kwargs)

snapshot = st.session_state.get(snapshot_key)
if snapshot is None:
    if is_offline:
        st.info("Offline field mode is active. The deterministic workflow above is available now; click **Show offline source state** to record which external sources are intentionally disabled.")
    else:
        st.info("Click **Refresh live sources** to load the situational layer. The deterministic relocation workflow above is already available offline.")
else:
    if snapshot.get("offline"):
        st.warning("Offline field mode: no current network observations were requested. External sources below are explicitly marked OFFLINE.")
    sources = snapshot["sources"]
    weather = sources["weather"]
    air = sources["air_quality"]
    current_weather = weather.get("current", {}) or {}
    current_air = air.get("current", {}) or {}
    weather_units = weather.get("current_units", {}) or {}
    air_units = air.get("current_units", {}) or {}
    health_df = pd.DataFrame(snapshot["source_health"])

    mode_values = health_df.get("mode", pd.Series(dtype=str)).astype(str).str.upper()
    access_values = health_df.get("access_status", pd.Series(dtype=str)).astype(str).str.upper()
    stale_values = health_df.get("stale", pd.Series(dtype=bool)).astype(str).str.lower()
    error_values = health_df.get("error", pd.Series(dtype=str)).fillna("").astype(str).str.strip()
    usable_count = int(mode_values.isin(["LIVE", "CACHED"]).sum())
    offline_count = int(access_values.eq("OFFLINE").sum())
    stale_count = int(stale_values.eq("true").sum())
    error_count = int(error_values.ne("").sum())
    render_kpi_strip([
        ("Usable Sources", usable_count, "LIVE or CACHED context"),
        ("Offline-disabled", offline_count, "Intentionally unavailable offline"),
        ("Stale Cache", stale_count, "Cached source marked stale"),
        ("Needs Attention", error_count, "Sources reporting an error"),
    ])

    temperature = current_weather.get("temperature_2m")
    precipitation = current_weather.get("precipitation")
    wind = current_weather.get("wind_speed_10m")
    aqi = current_air.get("us_aqi")
    pm25 = current_air.get("pm2_5")
    render_kpi_strip([
        ("Temperature", f"{temperature} {weather_units.get('temperature_2m', '')}" if temperature is not None else "—", "Current source value"),
        ("Precipitation", f"{precipitation} {weather_units.get('precipitation', '')}" if precipitation is not None else "—", "Current source value"),
        ("Wind", f"{wind} {weather_units.get('wind_speed_10m', '')}" if wind is not None else "—", "10 m wind speed"),
        ("US AQI", aqi if aqi is not None else "—", "Air-quality context"),
        ("PM2.5", f"{pm25} {air_units.get('pm2_5', '')}" if pm25 is not None else "—", "Air-quality context"),
        ("Nearby Events", len(snapshot["events"]), "Matching query window"),
    ])

    with st.expander("Per-source status", expanded=False):
        health_lookup = {row["source"]: row for row in snapshot["source_health"]}
        source_status = st.columns(4, gap="small")
        for index, (key, label) in enumerate([
            ("weather", "Weather"),
            ("air_quality", "Air"),
            ("usgs", "USGS"),
            ("gdacs", "GDACS"),
            ("eonet", "EONET"),
            ("imd", "IMD"),
            ("sachet", "SACHET"),
        ]):
            with source_status[index % len(source_status)]:
                st.markdown(f"**{label}**")
                if health_lookup[key].get("access_status") == "OFFLINE":
                    st.caption("OFFLINE")
                else:
                    render_data_mode_indicator(health_lookup[key]["mode"])
                    if health_lookup[key].get("stale"):
                        st.caption("STALE CACHE")

    event_col, health_col = st.columns([1.45, 1], gap="large")
    with event_col:
        st.markdown("### Nearby event register")
        events = pd.DataFrame(snapshot["events"])
        if events.empty:
            message = "No live event register is loaded in offline mode." if snapshot.get("offline") else "No matching nearby event was returned for the selected time/radius window."
            st.info(message)
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
        if not health_df.empty:
            st.dataframe(health_df.astype(str), width="stretch", hide_index=True)
        st.caption(f"Snapshot generated: {snapshot['generated_at']}")
        st.warning("External observations are corroborating evidence only until a verified source-specific calibration is approved for analytical scoring.")

with st.expander("Operator workflow · 5 steps", expanded=False):
    workflow = st.columns(5, gap="small")
    steps = [
        ("01", "Detect", "Refresh source context when connected; preserve explicit offline state when disconnected."),
        ("02", "Prioritize", "Use explainable risk and relocation priority."),
        ("03", "Validate", "Reject unsafe/full sites and inspect capacity evidence."),
        ("04", "Move", "Select a safe candidate and verify route provenance."),
        ("05", "Brief", "Export a reviewable draft action plan with assumptions."),
    ]
    for column, (number, title, text) in zip(workflow, steps):
        with column:
            render_source_card(f"{number} · {title}", "EOC step", text)

render_disclaimer()
