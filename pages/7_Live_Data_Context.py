import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.live_operations import fetch_operations_snapshot
from src.location_context import search_locations
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_page_header, render_source_card

st.set_page_config(page_title="Live Data Explorer", page_icon="LIVE", layout="wide")
inject_global_css()
render_page_header(
    "Live Data Explorer",
    "Fast, source-labelled situational awareness for the active operational area or any searched location.",
)

st.info(
    "Live weather, air quality and disaster-event feeds are fetched concurrently. They remain CONTEXT_ONLY and never silently alter H/E/V/A or the frozen risk score."
)

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.sidebar.warning(f"Configured operational feeds could not be resolved: {exc}")

with st.sidebar:
    st.subheader("Location")
    source_options = ["Search any location"]
    if resolved:
        source_options.insert(0, "Operational workspace")
    location_mode = st.radio("Context source", source_options, index=0)

location = None
if location_mode == "Operational workspace" and resolved:
    payload = resolved["payload"]
    center = payload["center"]
    location = {
        "name": payload.get("label", "Operational area"),
        "label": payload.get("label", "Operational area"),
        "latitude": float(center["latitude"]),
        "longitude": float(center["longitude"]),
    }
    st.success(f"Using operational workspace: **{location['label']}**")
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

st.markdown("### Query window")
settings = st.columns(3)
with settings[0]:
    days = st.slider("Look-back days", 1, 90, 14)
with settings[1]:
    radius_km = st.slider("Event radius (km)", 100, 1500, 500, 50)
with settings[2]:
    min_magnitude = st.slider("Minimum earthquake magnitude", 0.0, 6.0, 2.5, 0.5)

if location:
    st.caption(f"Selected: **{location['label']}** · {float(location['latitude']):.4f}, {float(location['longitude']):.4f}")

source_cols = st.columns(4, gap="small")
with source_cols[0]:
    render_source_card("Open-Meteo", "Weather + air", "Current meteorological and air-quality context at the selected coordinates.")
with source_cols[1]:
    render_source_card("USGS", "Earthquakes", "Recent earthquake events around the selected operational geography.")
with source_cols[2]:
    render_source_card("GDACS + EONET", "Disaster events", "Nearby global disaster and natural-event context, spatially filtered.")
with source_cols[3]:
    render_source_card("IMD + SACHET", "India official context", "Visible authorization/feed status; no credentials are bypassed or fabricated.")

refresh = st.button("Refresh live situational context", type="primary", width="stretch", disabled=location is None)

snapshot_key = None
if location:
    snapshot_key = f"live_explorer_{location['label']}_{days}_{radius_km}_{min_magnitude}"

if refresh and location:
    with st.spinner("Refreshing independent sources in parallel..."):
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
    st.markdown("### Ready")
    st.write("Select a location and refresh the live sources. No network calls are made while you are only adjusting controls.")
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

st.markdown("## Current operational context")
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

st.markdown("### Source health")
health_df = pd.DataFrame(snapshot.get("source_health", []))
if not health_df.empty:
    source_status = st.columns(min(7, len(health_df)), gap="small")
    for col, row in zip(source_status, health_df.to_dict(orient="records")):
        with col:
            st.markdown(f"**{row.get('source', 'source').upper()}**")
            render_data_mode_indicator(str(row.get("mode", "DEMO")))
            if str(row.get("stale", "False")).lower() == "true":
                st.caption("STALE CACHE")

lat = float(snapshot["latitude"])
lon = float(snapshot["longitude"])
map_obj = folium.Map(location=[lat, lon], zoom_start=7 if radius_km <= 500 else 6, tiles=None, control_scale=True)
folium.TileLayer(
    tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr="© OpenStreetMap contributors",
    name="OpenStreetMap",
    overlay=False,
    control=False,
).add_to(map_obj)
folium.Circle([lat, lon], radius=radius_km * 1000, color="#5d9cec", fill=False, weight=2, tooltip=f"Search radius: {radius_km} km").add_to(map_obj)
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

st.markdown("### Nearby event map")
st_folium(map_obj, height=480, width=1400, returned_objects=[])
st.caption("The radius circle is the query window, not a hazard boundary or statutory red zone.")

if events.empty:
    st.success("No matching nearby event was returned for this query window. Weather and source diagnostics remain useful context.")
else:
    st.markdown("### Nearby event register")
    show_cols = [c for c in ["source", "type", "event", "magnitude", "distance_km", "time", "latitude", "longitude", "url"] if c in events.columns]
    st.dataframe(events[show_cols], width="stretch", hide_index=True)
    st.download_button("Download nearby events (CSV)", events.to_csv(index=False).encode("utf-8"), "nearby_live_events.csv", "text/csv", width="stretch")

st.divider()
tabs = st.tabs(["Weather", "Air Quality", "USGS", "GDACS", "NASA EONET", "IMD", "NDMA SACHET", "Diagnostics"])

with tabs[0]:
    if weather_current:
        table = pd.DataFrame({"Variable": list(weather_current.keys()), "Value": [str(v) for v in weather_current.values()]})
        st.dataframe(table, width="stretch", hide_index=True)
    else:
        st.info("No current weather response is available.")

with tabs[1]:
    if air_current:
        table = pd.DataFrame({"Variable": list(air_current.keys()), "Value": [str(v) for v in air_current.values()]})
        st.dataframe(table, width="stretch", hide_index=True)
    else:
        st.info("No current air-quality response is available.")

with tabs[2]:
    df = pd.DataFrame(usgs.get("events", []))
    st.dataframe(df.astype(str), width="stretch", hide_index=True) if not df.empty else st.info("No USGS event matched the query.")

with tabs[3]:
    df = pd.DataFrame(gdacs.get("events", []))
    st.dataframe(df.astype(str), width="stretch", hide_index=True) if not df.empty else st.info("No nearby GDACS event matched the query.")

with tabs[4]:
    df = pd.DataFrame(eonet.get("events", []))
    st.dataframe(df.astype(str), width="stretch", hide_index=True) if not df.empty else st.info("No nearby EONET event matched the query.")

with tabs[5]:
    access_status = imd.get("access_status")
    if access_status == "AUTHORIZATION_REQUIRED":
        st.warning("IMD endpoint is reachable but this deployment/client is not yet authorized. Configure approved access when IMD grants it.")
    elif access_status == "LOCATION_NOT_MAPPED":
        st.info("IMD district mapping is not guessed for arbitrary locations. A verified district/state mapping is required.")
    warnings = pd.DataFrame(imd.get("warnings", []))
    rainfall = pd.DataFrame(imd.get("rainfall", []))
    if not warnings.empty:
        st.markdown("#### Warnings")
        st.dataframe(warnings.astype(str), width="stretch", hide_index=True)
    if not rainfall.empty:
        st.markdown("#### Rainfall")
        st.dataframe(rainfall.astype(str), width="stretch", hide_index=True)
    if warnings.empty and rainfall.empty and not access_status:
        st.info("No IMD rows were returned for this scope.")

with tabs[6]:
    alerts = pd.DataFrame(sachet.get("alerts", []))
    if alerts.empty:
        st.info("No verified SACHET alerts returned from the configured feed.")
    else:
        st.dataframe(alerts.astype(str), width="stretch", hide_index=True)
    st.caption("SACHET is LIVE only when a verified CAP/RSS feed identifier or URL is configured.")

with tabs[7]:
    if health_df.empty:
        st.info("No source diagnostics were generated.")
    else:
        st.dataframe(health_df.astype(str), width="stretch", hide_index=True)
    st.caption(f"Snapshot generated: {snapshot.get('generated_at')} · Analytical effect: {snapshot.get('analytical_effect')}")

st.warning("This page provides situational evidence only. It does not issue evacuation orders and does not convert uncalibrated live observations into risk scores.")
render_disclaimer()
