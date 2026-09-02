import streamlit as st

from src.operational_hazards import fetch_configured_hazard, validate_geojson_hazard
from src.streamlit_workspace import resolve_operational_hazard
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_page_header

st.set_page_config(page_title="Hazard Source", page_icon="HAZ", layout="wide")
inject_global_css()
render_page_header(
    "Calibrated Hazard Source",
    "Activate a reviewed public GeoJSON hazard feed for the analytical H component without hard-coding a study city.",
)

st.warning(
    "This page is intentionally calibration-gated. A reachable WFS/ArcGIS/GeoJSON endpoint is not enough: every feature must carry hazard_score 0–100 and the source-specific mapping must be documented before activation."
)

nav = st.columns(3)
with nav[0]:
    st.page_link("pages/10_GIS_Source_Inspector.py", label="Discover GIS source", use_container_width=True)
with nav[1]:
    st.page_link("pages/9_Operational_Data.py", label="Operational Data", use_container_width=True)
with nav[2]:
    st.page_link("pages/2_Red_Zone_Map.py", label="Red Zone Map", use_container_width=True)

st.markdown("### Current hazard source")
try:
    active = resolve_operational_hazard(auto_configured=True)
except Exception as exc:
    active = None
    st.warning(f"Configured hazard source could not be resolved: {exc}")

if active:
    cols = st.columns(5)
    cols[0].metric("Source", str(active.get("label") or "Calibrated hazard"))
    cols[1].metric("Origin", str(active.get("origin") or "session").replace("_", " ").title())
    cols[2].metric("Mode", active.get("mode") or "SESSION")
    cols[3].metric("Features", active.get("feature_count") or "—")
    cols[4].metric("Stale", "Yes" if active.get("stale") else "No")
    if active.get("mode") in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(active["mode"])
else:
    st.info("No calibrated hazard GeoJSON is active for this browser session or deployment configuration.")

st.divider()
st.markdown("### Activate a public HTTPS GeoJSON feed")
st.caption(
    "You may paste a direct GeoJSON URL or a bounded WFS/ArcGIS GeoJSON query URL from the GIS Source Inspector. "
    "Do not paste private tokens in the URL. Local/private-network targets and embedded credentials are rejected."
)

source_url = st.text_input(
    "Calibrated hazard GeoJSON HTTPS URL",
    placeholder="https://agency.example.gov.in/.../hazard.geojson",
)
source_label = st.text_input(
    "Source / layer label",
    placeholder="Agency · hazard type · layer name · reference period",
)
confirmed = st.checkbox(
    "I confirm the source owner, reference period, CRS/coverage, legend/classes and class/value → 0–100 hazard_score mapping are documented and approved for this analytical use",
    value=False,
)

if st.button(
    "Fetch, validate and activate calibrated hazard",
    type="primary",
    width="stretch",
    disabled=not (source_url.strip() and source_label.strip() and confirmed),
):
    try:
        with st.spinner("Fetching and validating calibrated hazard GeoJSON..."):
            result = fetch_configured_hazard(
                source_url.strip(),
                calibration_confirmed=True,
                source_label=source_label.strip(),
            )
            checked = validate_geojson_hazard(result["geojson"])
        st.session_state["operational_hazard_geojson"] = result["geojson"]
        st.session_state["operational_hazard_name"] = source_label.strip()
        st.session_state["operational_hazard_feed_status"] = {
            key: result.get(key)
            for key in ["mode", "stale", "fetched_at", "source_url", "label", "feature_count"]
        }
        st.success(f"Calibrated hazard source activated · {checked['feature_count']} feature(s).")
        st.rerun()
    except Exception as exc:
        st.error(f"Hazard source activation failed: {exc}")

status = st.session_state.get("operational_hazard_feed_status")
if status:
    with st.expander("Active hazard provenance", expanded=False):
        st.json(status)

if st.button("Clear browser-session hazard source", type="secondary"):
    for key in ["operational_hazard_geojson", "operational_hazard_name", "operational_hazard_feed_status"]:
        st.session_state.pop(key, None)
    st.rerun()

st.info(
    "After activation, choose Stored / calibrated GIS on Operational Data, Red Zone Map, Risk Analysis or Relocation Planner. The frozen H/E/V/A weights and risk classes remain unchanged."
)
render_disclaimer()
