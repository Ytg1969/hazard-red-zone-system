import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.earthquake_context import CITY_CENTERS
from src.live_operations import fetch_operations_snapshot
from src.location_context import search_locations
from src.runtime_mode import offline_mode
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_page_header

st.set_page_config(page_title="Live Context", page_icon="LIVE", layout="wide", initial_sidebar_state="auto")
inject_global_css()
render_page_header(
    "Live Context",
    "Source-labelled situational evidence for the active operational area without silently changing the deterministic risk model.",
)

offline = offline_mode()
if offline:
    st.info("Offline field mode is active. External source calls and online map tiles are disabled; local planning remains available.")
else:
    st.caption("Weather, air quality and disaster-event sources refresh only when requested. All observations remain CONTEXT_ONLY until explicitly calibrated.")

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.sidebar.warning(f"Configured operational feeds could not be resolved: {exc}")

location = None
with st.sidebar:
    st.subheader("Location")
    if resolved:
        location_mode = st.radio("Context source", ["Operational workspace", "Another location"], index=0)
    else:
        location_mode = "Another location"

if location_mode == "Operational workspace" and resolved:
    payload = resolved["payload"]
    center = payload["center"]
    location = {
        "name": payload.get("label", "Operational area"),
        "label": payload.get("label", "Operational area"),
        "latitude": float(center["latitude"]),
        "longitude": float(center["longitude"]),
    }
else:
    if offline:
        reference_names = [name for name in ["Puri", "Guwahati", "Chennai"] if name in CITY_CENTERS]
        selected_reference = st.selectbox("Offline reference location", reference_names)
        lat, lon = CITY_CENTERS[selected_reference]
        location = {
            "name": selected_reference,
            "label": selected_reference,
            "latitude": float(lat),
            "longitude": float(lon),
        }
        st.caption("Offline lookup is intentionally limited to bundled reference geographies unless an operational workspace is active.")
    else:
        search_left, search_right = st.columns([3, 1])
        with search_left:
            query = st.text_input("Search city / district / place", placeholder="e.g. Wayanad, Kerala or Guwahati, Assam")
        with search_right:
            st.write("")
            search_clicked = st.button("Search", width="stretch")
        if search_clicked and query.strip():
            try:
                result = search_locations(query, count=10)
                st.session_state["live_location_results"] = result.get("results", [])
            except Exception as exc:
                st.session_state["live_location_results"] = []
                st.error(f"Location search failed: {exc}")
        candidates = st.session_state.get("live_location_results", [])
        if candidates:
            labels = [item["label"] for item in candidates]
            chosen = st.selectbox("Matching location", labels)
            location = next(item for item in candidates if item["label"] == chosen)
        elif query:
            st.caption("Search to resolve the place to WGS84 coordinates.")

with st.sidebar.expander("Query window", expanded=False):
    days = st.slider("Look-back days", 1, 90, 14)
    radius_km = st.slider("Event radius (km)", 100, 1500, 500, 50)
    min_magnitude = st.slider("Minimum earthquake magnitude", 0.0, 6.0, 2.5, 0.5)

if location:
    st.caption(f"Selected context: **{location['label']}** · {float(location['latitude']):.4f}, {float(location['longitude']):.4f}")

refresh_label = "Load offline source state" if offline else "Refresh situational context"
refresh = st.button(refresh_label, type="primary", width="stretch", disabled=location is None)

snapshot_key = None
if location:
    snapshot_key = f"live_explorer_{location['label']}_{days}_{radius_km}_{min_magnitude}_{'offline' if offline else 'online'}"

if refresh and location:
    spinner_text = "Preparing offline source state..." if offline else "Refreshing independent sources in parallel..."
    with st.spinner(spinner_text):
        st.session_state[snapshot_key] = fetch_operations_snapshot(
            str(location["label"]),
            latitude=float(location["latitude"]),
            longitude=float(location["longitude"]),
            days=days,
            radius_km=radius_km,
            min_magnitude=min_magnitude,
        )

snapshot = st.session_state.get(snapshot_key) if snapshot_key else None
if snapshot is None:
    st.markdown("### Situational layer ready")
    if offline:
        st.write("Load the offline source state to confirm that external feeds are disabled. The risk, red-zone and relocation workflows do not depend on this page.")
    else:
        st.write("Choose a location and refresh when current corroborating evidence is needed. No source request is made while you are only adjusting controls.")
    with st.expander("What this page can show", expanded=False):
        st.markdown(
            "- Open-Meteo weather and air-quality context\n"
            "- USGS earthquake events and nearby GDACS / NASA EONET events\n"
            "- IMD and NDMA SACHET access/feed status where configured\n"
            "- Explicit LIVE / CACHED / DEMO / OFFLINE provenance without changing H/E/V/A"
        )
    render_disclaimer()
    st.stop()

sources = snapshot["sources"]
weather = sources.get("weather", {})
air = sources.get("air_quality", {})
usgs = sources.get("usgs", {})
gdacs = sources.get("gdacs", {})
eonet = sources.get("eonet", {})
imd = sources.get("imd", {})
sachet = sources.get("sachet", {})
weather_current = weather.get("current", {}) or {}
air_current = air.get("current", {}) or {}
weather_units = weather.get("current_units", {}) or {}
air_units = air.get("current_units", {}) or {}
events = pd.DataFrame(snapshot.get("events", []))
health_df = pd.DataFrame(snapshot.get("source_health", []))

st.markdown("## Current picture")
metrics = st.columns(6, gap="small")
temp = weather_current.get("temperature_2m")
precip = weather_current.get("precipitation")
wind = weather_current.get("wind_speed_10m")
aqi = air_current.get("us_aqi")
pm25 = air_current.get("pm2_5")
metrics[0].metric("Temperature", f"{temp} {weather_units.get('temperature_2m', '')}" if temp is not None else "—")
metrics[1].metric("Precipitation", f"{precip} {weather_units.get('precipitation', '')}" if precip is not None else "—")
metrics[2].metric("Wind", f"{wind} {weather_units.get('wind_speed_10m', '')}" if wind is not None else "—")
metrics[3].metric("US AQI", aqi if aqi is not None else "—")
metrics[4].metric("PM2.5", f"{pm25} {air_units.get('pm2_5', '')}" if pm25 is not None else "—")
metrics[5].metric("Nearby Events", len(events))

if not health_df.empty:
    mode_values = health_df.get("mode", pd.Series(dtype=str)).astype(str).str.upper()
    live_count = int(mode_values.isin(["LIVE", "CACHED"]).sum())
    offline_count = int(health_df.get("access_status", pd.Series(dtype=str)).astype(str).str.upper().eq("OFFLINE").sum())
    error_count = int(health_df.get("error", pd.Series(dtype=str)).fillna("").astype(str).str.strip().ne("").sum())
    status_cols = st.columns(3)
    status_cols[0].metric("Current / cached sources", live_count)
    status_cols[1].metric("Offline-disabled sources", offline_count)
    status_cols[2].metric("Sources needing attention", error_count)

lat = float(snapshot["latitude"])
lon = float(snapshot["longitude"])
map_obj = folium.Map(location=[lat, lon], zoom_start=7 if radius_km <= 500 else 6, tiles=None, control_scale=True)
if not offline:
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors",
        name="OpenStreetMap",
        overlay=False,
        control=False,
    ).add_to(map_obj)
folium.Circle([lat, lon], radius=radius_km * 1000, color="#5d9cec", fill=False, weight=2, tooltip=f"Query radius: {radius_km} km").add_to(map_obj)
folium.Marker([lat, lon], tooltip=str(location["label"]), icon=folium.Icon(color="blue", icon="info-sign")).add_to(map_obj)

if not events.empty:
    marker_colors = {"USGS": "purple", "GDACS": "orange", "NASA EONET": "green"}
    for row in events.head(100).to_dict(orient="records"):
        try:
            event_lat = float(row.get("latitude"))
            event_lon = float(row.get("longitude"))
        except (TypeError, ValueError):
            continue
        folium.CircleMarker(
            [event_lat, event_lon],
            radius=6,
            color=marker_colors.get(str(row.get("source")), "gray"),
            fill=True,
            fill_opacity=0.85,
            tooltip=f"{row.get('source')} · {row.get('event')} · {row.get('distance_km')} km",
        ).add_to(map_obj)

st.markdown("### Nearby event view")
st_folium(map_obj, height=430, width=1400, returned_objects=[])
if offline:
    st.caption("Offline mode intentionally omits internet basemap tiles. The query radius and any locally available vector/event geometry remain visible.")
else:
    st.caption("The radius circle is the query window, not a hazard boundary or statutory red zone.")

if events.empty:
    st.success("No matching nearby event is present in this source state. Missing live observations are not converted into risk values.")
else:
    with st.expander(f"Nearby event register · {len(events)} record(s)", expanded=False):
        show_cols = [c for c in ["source", "type", "event", "magnitude", "distance_km", "time", "latitude", "longitude", "url"] if c in events.columns]
        st.dataframe(events[show_cols], width="stretch", hide_index=True)
        st.download_button("Download nearby events (CSV)", events.to_csv(index=False).encode("utf-8"), "nearby_live_events.csv", "text/csv", width="stretch")

with st.expander("Source status", expanded=False):
    if health_df.empty:
        st.info("No source diagnostics were generated.")
    else:
        source_status = st.columns(min(4, len(health_df)), gap="small")
        for index, row in enumerate(health_df.to_dict(orient="records")):
            with source_status[index % len(source_status)]:
                st.markdown(f"**{str(row.get('source', 'source')).upper()}**")
                render_data_mode_indicator(str(row.get("mode", "DEMO")))
                access_status = str(row.get("access_status") or "").strip()
                if access_status and access_status not in {"None", "nan"}:
                    st.caption(access_status.replace("_", " ").title())
                if bool(row.get("stale", False)):
                    st.caption("STALE CACHE")

with st.expander("Weather and air-quality details", expanded=False):
    detail_left, detail_right = st.columns(2)
    with detail_left:
        st.markdown("#### Weather")
        if weather_current:
            table = pd.DataFrame({"Variable": list(weather_current.keys()), "Value": [str(v) for v in weather_current.values()]})
            st.dataframe(table, width="stretch", hide_index=True)
        else:
            st.info("No current weather response is available.")
    with detail_right:
        st.markdown("#### Air quality")
        if air_current:
            table = pd.DataFrame({"Variable": list(air_current.keys()), "Value": [str(v) for v in air_current.values()]})
            st.dataframe(table, width="stretch", hide_index=True)
        else:
            st.info("No current air-quality response is available.")

with st.expander("Global event-source details", expanded=False):
    for title, payload in [("USGS", usgs), ("GDACS", gdacs), ("NASA EONET", eonet)]:
        st.markdown(f"#### {title}")
        df = pd.DataFrame(payload.get("events", []))
        if df.empty:
            st.info(f"No {title} event matched the query.")
        else:
            st.dataframe(df.astype(str), width="stretch", hide_index=True)

with st.expander("India official-source details", expanded=False):
    access_status = imd.get("access_status")
    if access_status == "AUTHORIZATION_REQUIRED":
        st.warning("IMD endpoint is reachable but this deployment/client is not yet authorized. Configure approved access only after IMD grants it.")
    elif access_status == "LOCATION_NOT_MAPPED":
        st.info("IMD district mapping is not guessed for arbitrary locations. A verified district/state mapping is required.")
    warnings = pd.DataFrame(imd.get("warnings", []))
    rainfall = pd.DataFrame(imd.get("rainfall", []))
    if not warnings.empty:
        st.markdown("#### IMD warnings")
        st.dataframe(warnings.astype(str), width="stretch", hide_index=True)
    if not rainfall.empty:
        st.markdown("#### IMD rainfall")
        st.dataframe(rainfall.astype(str), width="stretch", hide_index=True)
    alerts = pd.DataFrame(sachet.get("alerts", []))
    st.markdown("#### NDMA SACHET")
    if alerts.empty:
        st.info("No verified SACHET alerts returned from the configured feed.")
    else:
        st.dataframe(alerts.astype(str), width="stretch", hide_index=True)
    st.caption("SACHET is LIVE only when a verified CAP/RSS feed identifier or URL is configured.")

with st.expander("Diagnostics and provenance", expanded=False):
    if health_df.empty:
        st.info("No source diagnostics were generated.")
    else:
        st.dataframe(health_df.astype(str), width="stretch", hide_index=True)
    st.caption(f"Snapshot generated: {snapshot.get('generated_at')} · Analytical effect: {snapshot.get('analytical_effect')}")

st.warning("Situational evidence is advisory. It does not issue evacuation orders and uncalibrated observations never alter the deterministic risk score.")
render_disclaimer()
