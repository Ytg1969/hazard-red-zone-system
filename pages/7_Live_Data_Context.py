import pandas as pd
import streamlit as st

from src.earthquake_context import fetch_recent_earthquakes
from src.gdacs_context import fetch_gdacs_events
from src.imd_context import fetch_imd_context
from src.live_alerts import fetch_disaster_alerts
from src.open_meteo_context import fetch_weather_context
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_page_header,
    render_source_card,
)

st.set_page_config(page_title="Live Data Context", page_icon="LIVE", layout="wide")
inject_global_css()
render_page_header(
    "Live Data Context",
    "External situational context for weather, earthquakes, disaster events and national alerts. External feeds never silently change the deterministic risk score.",
)

st.info(
    "Presentation rule: the analytical DEMO remains deterministic and offline-safe. "
    "This page demonstrates LIVE/CACHED external context while keeping unavailable or restricted sources visibly separated."
)

city = st.selectbox("City context", ["Puri", "Guwahati", "Chennai"], index=0)
refresh = st.button("Refresh external sources", type="primary", width="stretch")

source_cols = st.columns(5, gap="small")
with source_cols[0]:
    render_source_card("IMD", "District warnings + rainfall", "Official documented API; may require authorized client/IP access.")
with source_cols[1]:
    render_source_card("Open-Meteo", "Current weather", "No-auth live weather context with cache fallback.")
with source_cols[2]:
    render_source_card("USGS FDSN", "Earthquakes", "Official earthquake catalogue near the selected demo city.")
with source_cols[3]:
    render_source_card("GDACS", "Multi-hazard events", "Global flood, cyclone, earthquake, drought and volcano event context.")
with source_cols[4]:
    render_source_card("NDMA SACHET", "CAP / RSS alerts", "ETag-aware cache path; verified feed identifier required for LIVE mode.")

st.divider()

if not refresh:
    st.markdown("### Ready to query")
    st.write(
        "Select a city and press **Refresh external sources**. The app will attempt live calls, reuse the last successful "
        "cache where available, and fail visibly instead of inventing observations."
    )
    st.markdown("#### Authoritative GIS integration path")
    st.write(
        "NRSC/ISRO Bhuvan exposes OGC WMS services for Flood Hazard and Flood Annual Layers. "
        "Exact production layer identifiers and source-class mapping remain gated before those layers can affect scoring."
    )
    render_disclaimer()
    st.stop()

with st.spinner("Querying external sources with cache-aware fallbacks..."):
    imd = fetch_imd_context(city)
    try:
        weather = fetch_weather_context(city)
    except Exception as exc:
        weather = {"source": "Open-Meteo Forecast API", "mode": "DEMO", "stale": False, "current": {}, "error": str(exc)}
    try:
        usgs = fetch_recent_earthquakes(city, days=30, radius_km=500, min_magnitude=2.5)
    except Exception as exc:
        usgs = {"source": "USGS FDSN Earthquake Catalog", "mode": "DEMO", "stale": False, "events": [], "error": str(exc)}
    try:
        gdacs = fetch_gdacs_events(days=7)
    except Exception as exc:
        gdacs = {"source": "GDACS", "mode": "DEMO", "stale": False, "events": [], "error": str(exc)}
    sachet = fetch_disaster_alerts()

st.markdown("## Source status")
status_cols = st.columns(5, gap="small")
with status_cols[0]:
    st.markdown("#### IMD")
    render_data_mode_indicator(imd["mode"])
    st.metric("Warnings", len(imd.get("warnings", [])))
    st.metric("Rainfall rows", len(imd.get("rainfall", [])))
    if imd.get("access_status") == "AUTHORIZATION_REQUIRED":
        st.warning("Endpoint reachable; direct API authorization is required for this client/IP.")
    elif imd.get("stale"):
        st.warning("Using cached IMD response.")

with status_cols[1]:
    st.markdown("#### Open-Meteo")
    render_data_mode_indicator(weather["mode"])
    current = weather.get("current", {})
    units = weather.get("current_units", {})
    temperature = current.get("temperature_2m")
    precipitation = current.get("precipitation")
    st.metric("Temperature", f"{temperature} {units.get('temperature_2m', '')}" if temperature is not None else "—")
    st.metric("Precipitation", f"{precipitation} {units.get('precipitation', '')}" if precipitation is not None else "—")
    if weather.get("stale"):
        st.warning("Using cached weather response.")

with status_cols[2]:
    st.markdown("#### USGS")
    render_data_mode_indicator(usgs["mode"])
    st.metric("Quakes / 30 days", len(usgs.get("events", [])))
    if usgs.get("stale"):
        st.warning("Using cached USGS response.")

with status_cols[3]:
    st.markdown("#### GDACS")
    render_data_mode_indicator(gdacs["mode"])
    st.metric("Events / 7 days", len(gdacs.get("events", [])))
    if gdacs.get("stale"):
        st.warning("Using cached GDACS response.")

with status_cols[4]:
    st.markdown("#### SACHET")
    render_data_mode_indicator(sachet["mode"])
    st.metric("Alerts", len(sachet.get("alerts", [])))
    if sachet.get("stale"):
        st.warning("Using cached alert feed.")
    if sachet["mode"] == "DEMO":
        st.caption("Verified feed identifier not configured.")

st.divider()

tabs = st.tabs(["Current Weather", "IMD", "USGS Earthquakes", "GDACS Events", "NDMA Alerts"])

with tabs[0]:
    current = weather.get("current", {})
    if not current:
        st.info("Live weather context is unavailable and no cache exists.")
        if weather.get("error"):
            st.caption(weather["error"])
    else:
        weather_table = pd.DataFrame([current]).T.reset_index()
        weather_table.columns = ["Variable", "Value"]
        st.dataframe(weather_table, width="stretch", hide_index=True)
        st.caption("Open-Meteo data is real external weather context, not an official Indian warning product and not a direct input to the frozen risk score.")

with tabs[1]:
    if imd.get("access_status") == "AUTHORIZATION_REQUIRED":
        st.warning(
            "The official IMD API endpoint responded, but this demo machine is not authorized for direct API access. "
            "This is shown explicitly rather than bypassing authentication or disabling security controls."
        )
    for error in imd.get("errors", []):
        st.caption(error)
    warnings = pd.DataFrame(imd.get("warnings", []))
    rainfall = pd.DataFrame(imd.get("rainfall", []))
    if not warnings.empty:
        st.markdown("#### District warnings")
        st.dataframe(warnings, width="stretch", hide_index=True)
    if not rainfall.empty:
        st.markdown("#### District rainfall")
        st.dataframe(rainfall, width="stretch", hide_index=True)
    if warnings.empty and rainfall.empty and imd.get("access_status") != "AUTHORIZATION_REQUIRED":
        st.info("No IMD rows are available from the current or cached response.")

with tabs[2]:
    earthquakes = pd.DataFrame(usgs.get("events", []))
    if earthquakes.empty:
        st.info("No matching earthquake events were returned, or the source could not be reached and no cache exists.")
    else:
        show = [column for column in ["magnitude", "place", "depth_km", "time", "latitude", "longitude"] if column in earthquakes.columns]
        st.dataframe(earthquakes[show], width="stretch", hide_index=True)
    st.caption("USGS FDSN data is contextual evidence only and does not directly modify the prototype hazard score.")

with tabs[3]:
    events = pd.DataFrame(gdacs.get("events", []))
    if events.empty:
        st.info("No GDACS events were returned for the selected seven-day query, or the source is unavailable and no cache exists.")
        if gdacs.get("error"):
            st.caption(gdacs["error"])
    else:
        show = [c for c in ["event_type", "name", "country", "alert_level", "severity", "from_date", "to_date", "latitude", "longitude"] if c in events.columns]
        st.dataframe(events[show], width="stretch", hide_index=True)
    st.caption("GDACS is supplemental global disaster-awareness context and remains separate from calibrated local risk scoring.")

with tabs[4]:
    alerts = pd.DataFrame(sachet.get("alerts", []))
    if alerts.empty:
        st.info("No alerts returned.")
    else:
        show = [column for column in ["event", "severity", "urgency", "area", "headline", "published"] if column in alerts.columns]
        st.dataframe(alerts[show], width="stretch", hide_index=True)
    st.caption(
        "NDMA's SACHET integration guide requires client-side caching/ETag-aware CAP XML consumption. "
        "The configured feed must be verified before LIVE labeling."
    )

st.divider()
st.markdown("### Operationalization status")
st.markdown(
    """
- **Current weather:** LIVE no-auth context available through Open-Meteo with cache fallback.
- **Earthquakes:** LIVE USGS FDSN context available.
- **Multi-hazard events:** GDACS event context available with cache fallback.
- **IMD warnings/rainfall:** official endpoints are integrated but may require authorized client/IP access; the app does not bypass that control.
- **Flood / cyclone / landslide GIS:** Bhuvan layer identifiers, legend/classes and CRS must be verified before scoring.
- **NDMA alerts:** SACHET ETag handling is ready; a verified feed identifier is still required for LIVE mode.
"""
)

render_disclaimer()
