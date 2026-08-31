import math

import pandas as pd
import streamlit as st

from src.earthquake_context import CITY_CENTERS, fetch_recent_earthquakes_at_location
from src.eonet_context import CATEGORY_MAP, fetch_eonet_events
from src.gdacs_context import fetch_gdacs_events
from src.imd_context import fetch_imd_context
from src.live_alerts import fetch_disaster_alerts
from src.location_context import search_locations
from src.open_meteo_context import fetch_weather_at_location
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_page_header,
    render_source_card,
)

st.set_page_config(page_title="Live Data Explorer", page_icon="LIVE", layout="wide")
inject_global_css()
render_page_header(
    "Live Data Explorer",
    "Explore external weather and disaster context for any city and selected calamity without silently changing the deterministic red-zone score.",
)

st.info(
    "This explorer is situational context, not an automatic risk-calibration layer. LIVE/CACHED source evidence stays visibly separate from the deterministic DEMO analysis."
)

CALAMITIES = [
    "All calamities",
    "Flood",
    "Cyclone / Severe Storm",
    "Earthquake",
    "Landslide",
    "Drought",
    "Wildfire",
    "Volcano",
    "Dust / Haze",
    "Snow",
    "Temperature Extremes",
]
GDACS_TYPE_MAP = {
    "Flood": {"FL"},
    "Cyclone / Severe Storm": {"TC"},
    "Earthquake": {"EQ"},
    "Drought": {"DR"},
    "Volcano": {"VO"},
}

st.markdown("### Explore a location")
mode_col, location_col, calamity_col = st.columns([0.9, 1.55, 1.25], gap="large")
with mode_col:
    location_mode = st.radio("Location mode", ["Demo city", "Any city"], horizontal=True)

location = None
if location_mode == "Demo city":
    with location_col:
        city = st.selectbox("City", list(CITY_CENTERS), index=0)
    lat, lon = CITY_CENTERS[city]
    location = {"name": city, "label": city, "latitude": lat, "longitude": lon, "country": "India"}
else:
    with location_col:
        query = st.text_input("Search any city", placeholder="e.g. Mumbai, India or Tokyo, Japan")
        search_clicked = st.button("Find city", width="stretch")
    if search_clicked and query.strip():
        try:
            result = search_locations(query, count=10)
            st.session_state["live_location_results"] = result.get("results", [])
            st.session_state["live_location_query"] = query
        except Exception as exc:
            st.session_state["live_location_results"] = []
            st.error(f"Location search failed: {exc}")
    candidates = st.session_state.get("live_location_results", [])
    if candidates:
        labels = [item["label"] for item in candidates]
        chosen = st.selectbox("Matching location", labels)
        location = next(item for item in candidates if item["label"] == chosen)
    else:
        st.caption("Search for a city first. Open-Meteo geocoding is used to resolve WGS84 coordinates.")

with calamity_col:
    calamity = st.selectbox("Calamity / event type", CALAMITIES)

settings_left, settings_mid, settings_right = st.columns(3)
with settings_left:
    days = st.slider("Look-back window (days)", 1, 90, 30)
with settings_mid:
    radius_km = st.slider("Regional search radius (km)", 100, 1500, 500, 100)
with settings_right:
    min_magnitude = st.slider("Minimum earthquake magnitude", 0.0, 6.0, 2.5, 0.5)

if location:
    st.markdown(
        f"**Selected:** {location['label']} · `{float(location['latitude']):.4f}, {float(location['longitude']):.4f}` · "
        f"**Context:** {calamity}"
    )

refresh = st.button("Refresh selected live context", type="primary", width="stretch", disabled=location is None)

st.markdown("### Connected context sources")
row1 = st.columns(4, gap="small")
with row1[0]:
    render_source_card("Open-Meteo", "Weather + forecast", "No-auth current weather for arbitrary coordinates with cache fallback.")
with row1[1]:
    render_source_card("USGS FDSN", "Earthquakes", "Official earthquake catalogue queried around the selected coordinates.")
with row1[2]:
    render_source_card("GDACS", "Global disaster events", "UN/EU-supported flood, cyclone, earthquake, drought and volcano event context.")
with row1[3]:
    render_source_card("NASA EONET", "Natural events", "NASA-curated flood, storms, landslides, wildfire, volcano and other event categories.")
row2 = st.columns(3, gap="small")
with row2[0]:
    render_source_card("IMD", "Indian warnings", "Official adapter retained for verified mapped demo districts; authorization may be required.")
with row2[1]:
    render_source_card("NDMA SACHET", "National alerts", "ETag-aware CAP/RSS integration; verified feed identifier required for LIVE mode.")
with row2[2]:
    render_source_card("Bhuvan", "GIS context", "Verified WMS layers remain available on the Red Zone Map and are not numerically reinterpreted here.")

if not refresh:
    st.markdown("### How to use the explorer")
    st.write(
        "Choose one of the bundled demo cities or search for any city, select a calamity, tune the time/radius controls, and refresh. "
        "Weather and earthquake calls use the selected coordinates; GDACS and NASA EONET are filtered to the selected event type where supported."
    )
    render_disclaimer()
    st.stop()

lat = float(location["latitude"])
lon = float(location["longitude"])
name = str(location["label"])

# Approximate a regional bounding box for event discovery. This is a query window,
# not an administrative or hazard boundary.
lat_delta = radius_km / 111.0
lon_scale = max(0.2, math.cos(math.radians(lat)))
lon_delta = radius_km / (111.0 * lon_scale)
bbox = (lon - lon_delta, lat + lat_delta, lon + lon_delta, lat - lat_delta)

with st.spinner("Querying external sources with cache-aware fallbacks..."):
    try:
        weather = fetch_weather_at_location(name, lat, lon)
    except Exception as exc:
        weather = {"source": "Open-Meteo Forecast API", "mode": "DEMO", "stale": False, "current": {}, "error": str(exc)}
    try:
        usgs = fetch_recent_earthquakes_at_location(name, lat, lon, days=days, radius_km=radius_km, min_magnitude=min_magnitude)
    except Exception as exc:
        usgs = {"source": "USGS FDSN Earthquake Catalog", "mode": "DEMO", "stale": False, "events": [], "error": str(exc)}
    try:
        gdacs = fetch_gdacs_events(days=days)
    except Exception as exc:
        gdacs = {"source": "GDACS", "mode": "DEMO", "stale": False, "events": [], "error": str(exc)}
    try:
        eonet = fetch_eonet_events(category=CATEGORY_MAP.get(calamity), days=days, limit=100, bbox=bbox)
    except Exception as exc:
        eonet = {"source": "NASA EONET", "mode": "DEMO", "stale": False, "events": [], "error": str(exc)}

    # IMD aliases are deliberately verified only for bundled Indian demo cities.
    if location_mode == "Demo city":
        imd = fetch_imd_context(location["name"])
    else:
        imd = {"source": "India Meteorological Department", "mode": "DEMO", "stale": False, "warnings": [], "rainfall": [], "access_status": "LOCATION_NOT_MAPPED"}
    sachet = fetch_disaster_alerts()

if calamity != "All calamities" and calamity in GDACS_TYPE_MAP:
    wanted = GDACS_TYPE_MAP[calamity]
    gdacs["events"] = [row for row in gdacs.get("events", []) if str(row.get("event_type") or "").upper() in wanted]
elif calamity not in {"All calamities", *GDACS_TYPE_MAP.keys()}:
    gdacs["events"] = []

st.markdown("## Source status")
status1 = st.columns(4, gap="small")
with status1[0]:
    st.markdown("#### Open-Meteo")
    render_data_mode_indicator(weather["mode"])
    current = weather.get("current", {})
    units = weather.get("current_units", {})
    temp = current.get("temperature_2m")
    rain = current.get("precipitation")
    st.metric("Temperature", f"{temp} {units.get('temperature_2m', '')}" if temp is not None else "—")
    st.metric("Precipitation", f"{rain} {units.get('precipitation', '')}" if rain is not None else "—")
with status1[1]:
    st.markdown("#### USGS")
    render_data_mode_indicator(usgs["mode"])
    st.metric(f"Quakes / {days} days", len(usgs.get("events", [])))
with status1[2]:
    st.markdown("#### GDACS")
    render_data_mode_indicator(gdacs["mode"])
    st.metric("Matching events", len(gdacs.get("events", [])))
with status1[3]:
    st.markdown("#### NASA EONET")
    render_data_mode_indicator(eonet["mode"])
    st.metric("Regional events", len(eonet.get("events", [])))

status2 = st.columns(2, gap="large")
with status2[0]:
    st.markdown("#### IMD")
    render_data_mode_indicator(imd["mode"])
    if imd.get("access_status") == "AUTHORIZATION_REQUIRED":
        st.warning("Endpoint reachable; direct API authorization is required for this client/IP.")
    elif imd.get("access_status") == "LOCATION_NOT_MAPPED":
        st.info("Arbitrary-city IMD district lookup is not guessed. Use the verified demo-city mappings or add an authoritative district mapping.")
    else:
        st.metric("Warnings", len(imd.get("warnings", [])))
with status2[1]:
    st.markdown("#### NDMA SACHET")
    render_data_mode_indicator(sachet["mode"])
    st.metric("Alerts", len(sachet.get("alerts", [])))

st.divider()
tabs = st.tabs(["Weather", "USGS Earthquakes", "GDACS", "NASA EONET", "IMD", "NDMA SACHET"])

with tabs[0]:
    current = weather.get("current", {})
    if current:
        table = pd.DataFrame([current]).T.reset_index()
        table.columns = ["Variable", "Value"]
        st.dataframe(table, width="stretch", hide_index=True)
    else:
        st.info("No current weather response is available.")
        if weather.get("error"):
            st.caption(weather["error"])
    st.caption("Open-Meteo is external weather context, not an official Indian warning product and not a direct risk-score input.")

with tabs[1]:
    earthquakes = pd.DataFrame(usgs.get("events", []))
    if earthquakes.empty:
        st.info("No matching earthquake events were returned for this radius, magnitude and time window.")
    else:
        show = [c for c in ["magnitude", "place", "depth_km", "time", "latitude", "longitude", "detail_url"] if c in earthquakes.columns]
        st.dataframe(earthquakes[show], width="stretch", hide_index=True)
    st.caption("USGS FDSN is queried around the selected city coordinates and remains contextual evidence only.")

with tabs[2]:
    events = pd.DataFrame(gdacs.get("events", []))
    if events.empty:
        st.info("No GDACS events match the selected calamity/time filter, or that calamity is not represented by the current GDACS adapter.")
    else:
        show = [c for c in ["event_type", "name", "country", "alert_level", "severity", "from_date", "to_date", "latitude", "longitude", "url"] if c in events.columns]
        st.dataframe(events[show], width="stretch", hide_index=True)
    st.caption("GDACS is global event awareness; rows are not automatically city-local unless independently verified by coordinates.")

with tabs[3]:
    events = pd.DataFrame(eonet.get("events", []))
    if events.empty:
        st.info("No NASA EONET events were returned inside the approximate regional query window for the selected category/time range.")
        if eonet.get("error"):
            st.caption(eonet["error"])
    else:
        show = [c for c in ["title", "categories", "latest_date", "magnitude", "magnitude_unit", "latitude", "longitude", "closed", "api_link"] if c in events.columns]
        st.dataframe(events[show], width="stretch", hide_index=True)
    st.caption("NASA EONET is a curated natural-event discovery source. The bounding box is a regional search window, not a hazard boundary.")

with tabs[4]:
    if imd.get("access_status") == "AUTHORIZATION_REQUIRED":
        st.warning("The official IMD endpoint responded but this client/IP is not authorized for direct API access.")
    elif imd.get("access_status") == "LOCATION_NOT_MAPPED":
        st.info("No arbitrary-city IMD alias was invented. Verified district mapping is required before querying this source for a custom city.")
    warnings = pd.DataFrame(imd.get("warnings", []))
    rainfall = pd.DataFrame(imd.get("rainfall", []))
    if not warnings.empty:
        st.markdown("#### District warnings")
        st.dataframe(warnings, width="stretch", hide_index=True)
    if not rainfall.empty:
        st.markdown("#### District rainfall")
        st.dataframe(rainfall, width="stretch", hide_index=True)

with tabs[5]:
    alerts = pd.DataFrame(sachet.get("alerts", []))
    if alerts.empty:
        st.info("No verified SACHET alerts returned from the configured feed.")
    else:
        show = [c for c in ["event", "severity", "urgency", "area", "headline", "published"] if c in alerts.columns]
        st.dataframe(alerts[show], width="stretch", hide_index=True)
    st.caption("SACHET remains LIVE only when a verified feed identifier is configured; the app never fabricates one.")

st.divider()
st.markdown("### Context boundary")
st.write(
    "The explorer can now investigate arbitrary cities and multiple calamities through coordinate-based weather/earthquake queries and global event feeds. "
    "These sources support situational awareness. They do not automatically overwrite the frozen risk equation or convert an external event into an evacuation order."
)
render_disclaimer()
