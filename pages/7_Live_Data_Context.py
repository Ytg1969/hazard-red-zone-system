import math

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.air_quality_context import fetch_air_quality_at_location
from src.earthquake_context import CITY_CENTERS, fetch_recent_earthquakes_at_location
from src.eonet_context import CATEGORY_MAP, fetch_eonet_events
from src.gdacs_context import fetch_gdacs_events
from src.imd_context import fetch_imd_context
from src.live_alerts import fetch_disaster_alerts
from src.location_context import search_locations
from src.open_meteo_context import fetch_weather_at_location
from src.spatial_analysis import haversine_km
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
    "Explore current weather, air quality and nearby disaster-event evidence for any city without silently changing the deterministic red-zone score.",
)

st.info(
    "Use this page for situational awareness: what is happening around a location right now or recently. "
    "A zero-event result is still useful—it means the selected source returned no matching nearby event in the chosen window."
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

st.markdown("### 1 · Choose location and calamity")
mode_col, location_col, calamity_col = st.columns([0.9, 1.55, 1.25], gap="large")
with mode_col:
    location_mode = st.radio("Location mode", ["Demo city", "Any city"], horizontal=True)

location = None
if location_mode == "Demo city":
    with location_col:
        city = st.selectbox("City", list(CITY_CENTERS), index=0)
    lat, lon = CITY_CENTERS[city]
    location = {"name": city, "label": f"{city}, India", "latitude": lat, "longitude": lon, "country": "India"}
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
        st.caption("Search for a city first; the geocoder resolves it to WGS84 coordinates.")

with calamity_col:
    calamity = st.selectbox("Calamity / event type", CALAMITIES)

preset = st.segmented_control(
    "Explorer preset",
    ["Balanced", "Local incident", "Regional watch"],
    default="Balanced",
)
if preset == "Local incident":
    default_days, default_radius = 7, 150
elif preset == "Regional watch":
    default_days, default_radius = 60, 1000
else:
    default_days, default_radius = 30, 500

settings_left, settings_mid, settings_right = st.columns(3)
with settings_left:
    days = st.slider("Look-back window (days)", 1, 90, default_days)
with settings_mid:
    radius_km = st.slider("Nearby-event radius (km)", 100, 1500, default_radius, 50)
with settings_right:
    min_magnitude = st.slider("Minimum earthquake magnitude", 0.0, 6.0, 2.5, 0.5)

if location:
    st.markdown(
        f"**Selected:** {location['label']} · `{float(location['latitude']):.4f}, {float(location['longitude']):.4f}` · "
        f"**Event focus:** {calamity}"
    )

refresh = st.button("Load live situational context", type="primary", width="stretch", disabled=location is None)

st.markdown("### 2 · What these sources are used for")
source_cols = st.columns(4, gap="small")
with source_cols[0]:
    render_source_card("Open-Meteo", "Weather now", "Temperature, precipitation, wind and gusts at the selected coordinates.")
with source_cols[1]:
    render_source_card("Open-Meteo Air", "Air / dust context", "AQI, PM2.5, PM10, dust and UV context useful during smoke, haze and heat events.")
with source_cols[2]:
    render_source_card("USGS + GDACS", "Recent events", "Nearby earthquakes plus global disaster events spatially checked against the selected city.")
with source_cols[3]:
    render_source_card("NASA EONET", "Regional natural events", "NASA-curated storms, floods, fires, landslides, volcanoes and related event metadata.")

st.caption(
    "IMD and NDMA SACHET remain available as official Indian-source integrations where authorization/feed mapping permits. "
    "Bhuvan authoritative/historical WMS layers remain on the Red Zone Map."
)

if not refresh:
    st.markdown("### 3 · Load the context")
    st.write(
        "Choose a location, optionally choose a calamity, and click **Load live situational context**. "
        "The page will show current measurements, source status, a nearby-event map and detailed source tabs."
    )
    render_disclaimer()
    st.stop()

lat = float(location["latitude"])
lon = float(location["longitude"])
name = str(location["label"])

lat_delta = radius_km / 111.0
lon_scale = max(0.2, math.cos(math.radians(lat)))
lon_delta = radius_km / (111.0 * lon_scale)
bbox = (lon - lon_delta, lat + lat_delta, lon + lon_delta, lat - lat_delta)

with st.spinner("Loading weather, air quality and disaster-event context..."):
    try:
        weather = fetch_weather_at_location(name, lat, lon)
    except Exception as exc:
        weather = {"source": "Open-Meteo Forecast API", "mode": "DEMO", "stale": False, "current": {}, "error": str(exc)}
    try:
        air = fetch_air_quality_at_location(name, lat, lon)
    except Exception as exc:
        air = {"source": "Open-Meteo Air Quality API", "mode": "DEMO", "stale": False, "current": {}, "error": str(exc)}
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

    if location_mode == "Demo city":
        imd = fetch_imd_context(location["name"])
    else:
        imd = {
            "source": "India Meteorological Department",
            "mode": "DEMO",
            "stale": False,
            "warnings": [],
            "rainfall": [],
            "access_status": "LOCATION_NOT_MAPPED",
        }
    sachet = fetch_disaster_alerts()

# Calamity filtering for GDACS, followed by a real coordinate-distance filter so
# the page does not present remote global events as if they were local.
gdacs_events = list(gdacs.get("events", []))
if calamity != "All calamities" and calamity in GDACS_TYPE_MAP:
    wanted = GDACS_TYPE_MAP[calamity]
    gdacs_events = [row for row in gdacs_events if str(row.get("event_type") or "").upper() in wanted]
elif calamity not in {"All calamities", *GDACS_TYPE_MAP.keys()}:
    gdacs_events = []

gdacs_nearby = []
for row in gdacs_events:
    try:
        event_lat = float(row.get("latitude"))
        event_lon = float(row.get("longitude"))
    except (TypeError, ValueError):
        continue
    if haversine_km(lat, lon, event_lat, event_lon) <= radius_km:
        local = dict(row)
        local["distance_km"] = round(haversine_km(lat, lon, event_lat, event_lon), 1)
        gdacs_nearby.append(local)

gdacs["events"] = gdacs_nearby

weather_current = weather.get("current", {})
weather_units = weather.get("current_units", {})
air_current = air.get("current", {})
air_units = air.get("current_units", {})

combined_events = []
for row in usgs.get("events", []):
    try:
        event_lat = float(row.get("latitude"))
        event_lon = float(row.get("longitude"))
    except (TypeError, ValueError):
        continue
    combined_events.append({
        "source": "USGS", "event": row.get("place") or "Earthquake", "type": "Earthquake",
        "latitude": event_lat, "longitude": event_lon,
        "distance_km": round(haversine_km(lat, lon, event_lat, event_lon), 1),
        "time": row.get("time"), "url": row.get("detail_url"),
    })
for row in gdacs_nearby:
    combined_events.append({
        "source": "GDACS", "event": row.get("name") or row.get("country") or "Disaster event",
        "type": row.get("event_type"), "latitude": row.get("latitude"), "longitude": row.get("longitude"),
        "distance_km": row.get("distance_km"), "time": row.get("from_date"), "url": row.get("url"),
    })
for row in eonet.get("events", []):
    try:
        event_lat = float(row.get("latitude"))
        event_lon = float(row.get("longitude"))
    except (TypeError, ValueError):
        continue
    combined_events.append({
        "source": "NASA EONET", "event": row.get("title") or "Natural event",
        "type": row.get("categories"), "latitude": event_lat, "longitude": event_lon,
        "distance_km": round(haversine_km(lat, lon, event_lat, event_lon), 1),
        "time": row.get("latest_date"), "url": row.get("api_link"),
    })
combined_events.sort(key=lambda item: float(item.get("distance_km") or 10**9))

st.markdown("## Operational context snapshot")
snapshot = st.columns(6, gap="small")
temp = weather_current.get("temperature_2m")
precip = weather_current.get("precipitation")
wind = weather_current.get("wind_speed_10m")
aqi = air_current.get("us_aqi")
pm25 = air_current.get("pm2_5")
snapshot[0].metric("Temperature", f"{temp} {weather_units.get('temperature_2m', '')}" if temp is not None else "—")
snapshot[1].metric("Precipitation", f"{precip} {weather_units.get('precipitation', '')}" if precip is not None else "—")
snapshot[2].metric("Wind", f"{wind} {weather_units.get('wind_speed_10m', '')}" if wind is not None else "—")
snapshot[3].metric("US AQI", aqi if aqi is not None else "—")
snapshot[4].metric("PM2.5", f"{pm25} {air_units.get('pm2_5', '')}" if pm25 is not None else "—")
snapshot[5].metric("Nearby Events", len(combined_events))

if combined_events:
    nearest = combined_events[0]
    st.info(
        f"Nearest observed event in the selected window: **{nearest['source']} · {nearest['event']}** "
        f"at approximately **{nearest['distance_km']} km**. This is context only, not an evacuation trigger."
    )
else:
    st.success("No matching nearby disaster event was returned in the selected time/radius window.")

# Lightweight operational interpretation; it intentionally does not alter risk scoring.
interpretation = []
if precip is not None and float(precip) > 0:
    interpretation.append("Current precipitation is being observed.")
if wind is not None and float(wind) >= 40:
    interpretation.append("Strong surface wind is present; field teams should verify local conditions.")
if aqi is not None and float(aqi) >= 101:
    interpretation.append("Air quality is elevated; consider exposure precautions for sensitive populations.")
if combined_events:
    interpretation.append(f"{len(combined_events)} external event record(s) fall inside the selected regional query context.")
if interpretation:
    with st.expander("Operational interpretation", expanded=True):
        for item in interpretation:
            st.write(f"• {item}")
        st.caption("These statements are situational cues only. They do not change the deterministic risk class or authorize evacuation.")

st.markdown("### Source health")
health = st.columns(6, gap="small")
for column, label, source in [
    (health[0], "Weather", weather),
    (health[1], "Air Quality", air),
    (health[2], "USGS", usgs),
    (health[3], "GDACS nearby", gdacs),
    (health[4], "NASA EONET", eonet),
    (health[5], "SACHET", sachet),
]:
    with column:
        st.markdown(f"**{label}**")
        render_data_mode_indicator(source.get("mode", "DEMO"))

st.markdown("### Nearby-event map")
event_map = folium.Map(location=[lat, lon], zoom_start=6 if radius_km >= 500 else 8, tiles=None, control_scale=True)
folium.TileLayer(
    tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    name="OpenStreetMap",
    overlay=False,
    control=False,
).add_to(event_map)
folium.Circle(
    [lat, lon], radius=radius_km * 1000.0, color="#1a73e8", weight=1.5,
    fill=False, opacity=0.45, tooltip=f"Regional query radius: {radius_km} km",
).add_to(event_map)
folium.Marker([lat, lon], tooltip=f"Selected location: {name}", icon=folium.Icon(color="blue", icon="info-sign")).add_to(event_map)

for row in usgs.get("events", []):
    try:
        event_lat = float(row.get("latitude"))
        event_lon = float(row.get("longitude"))
    except (TypeError, ValueError):
        continue
    folium.CircleMarker(
        [event_lat, event_lon], radius=6, color="#7e57c2", fill=True, fill_opacity=0.8,
        tooltip=f"USGS M{row.get('magnitude')} · {row.get('place', 'Earthquake')}",
    ).add_to(event_map)

for row in gdacs_nearby:
    try:
        event_lat = float(row.get("latitude"))
        event_lon = float(row.get("longitude"))
    except (TypeError, ValueError):
        continue
    folium.CircleMarker(
        [event_lat, event_lon], radius=7, color="#d84315", fill=True, fill_opacity=0.8,
        tooltip=f"GDACS {row.get('event_type', '')} · {row.get('name') or row.get('country') or 'Event'} · {row.get('distance_km')} km",
    ).add_to(event_map)

for row in eonet.get("events", []):
    try:
        event_lat = float(row.get("latitude"))
        event_lon = float(row.get("longitude"))
    except (TypeError, ValueError):
        continue
    folium.CircleMarker(
        [event_lat, event_lon], radius=7, color="#2e7d32", fill=True, fill_opacity=0.8,
        tooltip=f"NASA EONET · {row.get('title', 'Natural event')}",
    ).add_to(event_map)

st_folium(event_map, height=430, width=1400, returned_objects=[])
st.caption("Basemap: OpenStreetMap public tiles. No map API key or token is required.")

if not combined_events:
    st.success("No matching nearby disaster event was returned in the selected time/radius window. Weather and air-quality context are still shown above.")

if combined_events:
    events_df = pd.DataFrame(combined_events)
    st.markdown("### Nearby event register")
    show_cols = [c for c in ["source", "type", "event", "distance_km", "time", "latitude", "longitude", "url"] if c in events_df.columns]
    st.dataframe(events_df[show_cols], width="stretch", hide_index=True)
    st.download_button(
        "Download nearby events (CSV)",
        data=events_df.to_csv(index=False).encode("utf-8"),
        file_name="nearby_live_events.csv",
        mime="text/csv",
        width="stretch",
    )

st.divider()
tabs = st.tabs(["Weather", "Air Quality", "USGS Earthquakes", "GDACS Nearby", "NASA EONET", "IMD", "NDMA SACHET", "Diagnostics"])

with tabs[0]:
    if weather_current:
        table = pd.DataFrame([weather_current]).T.reset_index()
        table.columns = ["Variable", "Value"]
        st.dataframe(table, width="stretch", hide_index=True)
    else:
        st.info("No current weather response is available.")
        if weather.get("error"):
            st.caption(weather["error"])
    st.caption("Weather is real external context; it does not automatically alter the frozen red-zone risk score.")

with tabs[1]:
    if air_current:
        table = pd.DataFrame([air_current]).T.reset_index()
        table.columns = ["Variable", "Value"]
        st.dataframe(table, width="stretch", hide_index=True)
    else:
        st.info("No air-quality response is available.")
        if air.get("error"):
            st.caption(air["error"])
    st.caption("Air-quality values provide environmental context for haze, smoke, dust and heat operations; they are not a calibrated red-zone input.")

with tabs[2]:
    earthquakes = pd.DataFrame(usgs.get("events", []))
    if earthquakes.empty:
        st.info("No earthquake event matched this radius, magnitude and time window.")
    else:
        show = [c for c in ["magnitude", "place", "depth_km", "time", "latitude", "longitude", "detail_url"] if c in earthquakes.columns]
        st.dataframe(earthquakes[show], width="stretch", hide_index=True)

with tabs[3]:
    events = pd.DataFrame(gdacs_nearby)
    if events.empty:
        st.info("No GDACS event with usable coordinates matched the selected calamity and radius.")
    else:
        show = [c for c in ["event_type", "name", "country", "alert_level", "severity", "distance_km", "from_date", "to_date", "url"] if c in events.columns]
        st.dataframe(events[show], width="stretch", hide_index=True)
    st.caption("GDACS rows shown here are spatially filtered around the selected location rather than presented as generic global events.")

with tabs[4]:
    events = pd.DataFrame(eonet.get("events", []))
    if events.empty:
        st.info("No NASA EONET event was returned inside the selected regional window/category/time range.")
        if eonet.get("error"):
            st.caption(eonet["error"])
    else:
        show = [c for c in ["title", "categories", "latest_date", "magnitude", "magnitude_unit", "latitude", "longitude", "closed", "api_link"] if c in events.columns]
        st.dataframe(events[show], width="stretch", hide_index=True)

with tabs[5]:
    if imd.get("access_status") == "AUTHORIZATION_REQUIRED":
        st.warning("The official IMD endpoint responded but this client/IP is not authorized for direct API access.")
    elif imd.get("access_status") == "LOCATION_NOT_MAPPED":
        st.info("No arbitrary-city IMD district alias is guessed; verified district mapping is required.")
    warnings = pd.DataFrame(imd.get("warnings", []))
    rainfall = pd.DataFrame(imd.get("rainfall", []))
    if not warnings.empty:
        st.markdown("#### District warnings")
        st.dataframe(warnings, width="stretch", hide_index=True)
    if not rainfall.empty:
        st.markdown("#### District rainfall")
        st.dataframe(rainfall, width="stretch", hide_index=True)

with tabs[6]:
    alerts = pd.DataFrame(sachet.get("alerts", []))
    if alerts.empty:
        st.info("No verified SACHET alerts returned from the configured feed.")
    else:
        show = [c for c in ["event", "severity", "urgency", "area", "headline", "published"] if c in alerts.columns]
        st.dataframe(alerts[show], width="stretch", hide_index=True)
    st.caption("SACHET is labelled LIVE only when a verified feed identifier is configured.")

with tabs[7]:
    diagnostics = []
    for label, source in [
        ("Open-Meteo weather", weather), ("Open-Meteo air", air), ("USGS", usgs),
        ("GDACS", gdacs), ("NASA EONET", eonet), ("IMD", imd), ("NDMA SACHET", sachet),
    ]:
        diagnostics.append({
            "source": label,
            "mode": source.get("mode", "DEMO"),
            "stale": source.get("stale", False),
            "error": source.get("error"),
            "access_status": source.get("access_status"),
        })
    st.dataframe(pd.DataFrame(diagnostics), width="stretch", hide_index=True)
    st.caption("Use this tab during troubleshooting to distinguish a genuine zero-event result from an API/network/authorization issue.")

st.divider()
st.markdown("### How this helps the EOC")
st.write(
    "This page answers a different question from the Red Zone Map: **what external conditions and events are currently visible around the selected location?** "
    "The Red Zone Map remains the deterministic relocation decision workflow; the Live Data Explorer provides corroborating situational evidence and source provenance."
)
render_disclaimer()
