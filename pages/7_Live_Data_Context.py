import pandas as pd
import streamlit as st

from src.earthquake_context import fetch_recent_earthquakes
from src.imd_context import fetch_imd_context
from src.live_alerts import fetch_disaster_alerts
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
    "Verified external context for weather warnings, rainfall, earthquakes and national alerts. External feeds never silently change the deterministic risk score.",
)

st.info(
    "Presentation rule: the analytical DEMO remains deterministic and offline-safe. "
    "This page demonstrates how verified external sources can be consumed as LIVE/CACHED context."
)

city = st.selectbox("City context", ["Puri", "Guwahati", "Chennai"], index=0)
refresh = st.button("Refresh verified external sources", type="primary", width="stretch")

source_left, source_mid, source_right = st.columns(3, gap="large")
with source_left:
    render_source_card("India Meteorological Department", "District warnings + rainfall", "Official IMD endpoints with cache-aware LIVE/CACHED handling.")
with source_mid:
    render_source_card("USGS FDSN", "Earthquake catalogue", "Official radius/time-window query around the selected demo city.")
with source_right:
    render_source_card("NDMA SACHET", "CAP / RSS alerts", "ETag-aware cache path; verified feed identifier required for LIVE mode.")

st.divider()

if not refresh:
    st.markdown("### Ready to query")
    st.write(
        "Select a city and press **Refresh verified external sources**. The app will attempt live calls, "
        "reuse the last successful cache when available, and otherwise fail visibly instead of inventing observations."
    )
    st.markdown("#### Additional authoritative GIS integration path")
    st.write(
        "NRSC/ISRO Bhuvan exposes OGC WMS services for Flood Hazard and Flood Annual Layers. "
        "The service endpoint family is verified, while exact production layer identifiers and source-class mapping "
        "remain gated before those layers can affect hazard scoring."
    )
    render_disclaimer()
    st.stop()

with st.spinner("Querying verified sources with cache-aware fallbacks..."):
    imd = fetch_imd_context(city)
    try:
        usgs = fetch_recent_earthquakes(city, days=30, radius_km=500, min_magnitude=2.5)
    except Exception as exc:
        usgs = {
            "source": "USGS FDSN Earthquake Catalog",
            "mode": "DEMO",
            "stale": False,
            "events": [],
            "error": str(exc),
        }
    sachet = fetch_disaster_alerts()

st.markdown("## Source status")
status_cols = st.columns(3, gap="large")
with status_cols[0]:
    st.markdown("#### IMD Weather")
    render_data_mode_indicator(imd["mode"])
    st.metric("Matched warnings", len(imd.get("warnings", [])))
    st.metric("Matched rainfall rows", len(imd.get("rainfall", [])))
    if imd.get("stale"):
        st.warning("Using cached IMD response.")
    for error in imd.get("errors", []):
        st.caption(error)

with status_cols[1]:
    st.markdown("#### USGS Earthquakes")
    render_data_mode_indicator(usgs["mode"])
    st.metric("Events within 500 km / 30 days", len(usgs.get("events", [])))
    if usgs.get("stale"):
        st.warning("Using cached USGS response.")
    if usgs.get("error"):
        st.caption(usgs["error"])

with status_cols[2]:
    st.markdown("#### NDMA SACHET Alerts")
    render_data_mode_indicator(sachet["mode"])
    st.metric("Alerts displayed", len(sachet.get("alerts", [])))
    if sachet.get("stale"):
        st.warning("Using cached alert feed.")
    if sachet["mode"] == "DEMO":
        st.caption("Configure a verified SACHET CAP/RSS feed URL before claiming LIVE alerts.")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["IMD Warnings", "IMD Rainfall", "USGS Earthquakes", "NDMA Alerts"])

with tab1:
    warnings = pd.DataFrame(imd.get("warnings", []))
    if warnings.empty:
        st.info("No matching IMD warning rows were available for the selected city in the current/cached response.")
    else:
        st.dataframe(warnings, width="stretch", hide_index=True)
    st.caption("IMD warning codes and color levels are decoded using the official API documentation.")

with tab2:
    rainfall = pd.DataFrame(imd.get("rainfall", []))
    if rainfall.empty:
        st.info("No matching IMD district-rainfall row was available for the selected city in the current/cached response.")
    else:
        st.dataframe(rainfall, width="stretch", hide_index=True)
    st.caption("Rainfall fields are preserved from the source response rather than renamed into unsupported scientific claims.")

with tab3:
    earthquakes = pd.DataFrame(usgs.get("events", []))
    if earthquakes.empty:
        st.info("No matching earthquake events were returned, or the source could not be reached and no cache exists.")
    else:
        show = [column for column in ["magnitude", "place", "depth_km", "time", "latitude", "longitude"] if column in earthquakes.columns]
        st.dataframe(earthquakes[show], width="stretch", hide_index=True)
    st.caption("USGS FDSN data is contextual evidence only and does not directly modify the prototype hazard score.")

with tab4:
    alerts = pd.DataFrame(sachet.get("alerts", []))
    if alerts.empty:
        st.info("No alerts returned.")
    else:
        show = [column for column in ["event", "severity", "urgency", "area", "headline", "published"] if column in alerts.columns]
        st.dataframe(alerts[show], width="stretch", hide_index=True)
    st.caption(
        "NDMA's SACHET integration guide requires client-side caching/ETag-aware consumption for CAP XML. "
        "The configured feed must be verified before LIVE labeling."
    )

st.divider()
st.markdown("### What can become operational next")
st.markdown(
    """
- **Weather:** map verified IMD warning/rainfall fields into source-specific hazard rules only after calibration.
- **Flood / cyclone / landslide GIS:** verify exact Bhuvan layer identifiers, legend/classes and CRS before scoring.
- **Alerts:** configure the verified SACHET CAP/RSS identifier; ETag revalidation is already implemented.
- **Roads:** pre-cache local OSMnx graphs for Puri, Guwahati and Chennai so route comparisons remain usable offline.
"""
)

render_disclaimer()
