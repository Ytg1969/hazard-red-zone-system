import pandas as pd
import streamlit as st

from src.live_operations import fetch_operations_snapshot
from src.operational_hazards import geojson_to_gdf, validate_geojson_hazard
from src.operational_sources import configured_operational_urls, fetch_operational_habitations, fetch_operational_shelters
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters, serialize_workspace
from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_kpi_strip, render_page_header

st.set_page_config(page_title="Operational Data", page_icon="DATA", layout="wide")
inject_global_css()
render_page_header(
    "Operational Data Workspace",
    "Load authority/field habitation, relocation-site and calibrated hazard data; activate one shared workspace for map, risk and relocation modules.",
)

st.info("This is the transition path away from bundled demo cities. Reachability does not prove authority: source owner, update time, field definitions and hazard calibration must be verified.")

source_mode = st.segmented_control("Settlement/site source", ["Upload files", "Configured HTTPS feeds"], default="Upload files")
label = st.text_input("Operational area label", placeholder="e.g. Wayanad District, Kerala")

if source_mode == "Upload files":
    left, right = st.columns(2, gap="large")
    with left:
        habitation_upload = st.file_uploader("Habitation / settlement CSV", type=["csv"], key="ops_hab")
    with right:
        shelter_upload = st.file_uploader("Shelter / relocation-site CSV", type=["csv"], key="ops_shelter")
    activate = st.button("Validate and activate operational workspace", type="primary", width="stretch", disabled=not (habitation_upload and shelter_upload))
    if activate:
        try:
            habitations_raw, h_assessment = normalize_operational_habitations(pd.read_csv(habitation_upload))
            shelters_raw, s_assessment = normalize_operational_shelters(pd.read_csv(shelter_upload))
            st.session_state["operational_workspace"] = serialize_workspace(habitations_raw, shelters_raw, label=label or "Operational upload")
            st.session_state["operational_habitation_assessment"] = h_assessment
            st.session_state["operational_shelter_assessment"] = s_assessment
            st.success("Operational workspace activated for this browser session.")
        except Exception as exc:
            st.error(f"Could not activate operational data: {exc}")
else:
    configured = configured_operational_urls()
    c1, c2 = st.columns(2)
    c1.write("**Habitation feed:** " + ("configured" if configured["habitations"] else "not configured"))
    c2.write("**Shelter feed:** " + ("configured" if configured["shelters"] else "not configured"))
    st.caption("Deployment variables: `SIH_HABITATION_CSV_URL` and `SIH_SHELTER_CSV_URL`. URLs must use HTTPS.")
    refresh_feeds = st.button("Fetch, validate and activate configured feeds", type="primary", width="stretch", disabled=not (configured["habitations"] and configured["shelters"]))
    if refresh_feeds:
        try:
            with st.spinner("Fetching configured operational datasets..."):
                h_result = fetch_operational_habitations()
                s_result = fetch_operational_shelters()
            st.session_state["operational_workspace"] = serialize_workspace(h_result["data"], s_result["data"], label=label or "Configured operational feeds")
            st.session_state["operational_habitation_assessment"] = h_result["assessment"]
            st.session_state["operational_shelter_assessment"] = s_result["assessment"]
            st.session_state["operational_feed_status"] = {
                "habitations": {k: h_result[k] for k in ["mode", "stale", "fetched_at", "source_url"]},
                "shelters": {k: s_result[k] for k in ["mode", "stale", "fetched_at", "source_url"]},
            }
            st.success("Configured operational feeds activated.")
        except Exception as exc:
            st.error(f"Configured feed refresh failed: {exc}")

payload = st.session_state.get("operational_workspace")
if not payload:
    st.warning("No operational workspace is active yet. Upload both datasets or configure both HTTPS feeds.")
    render_disclaimer()
    st.stop()

habitations_raw = pd.DataFrame(payload["habitations"])
shelters_raw = pd.DataFrame(payload["shelters"])

meta = st.columns(4)
meta[0].metric("Operational area", payload["label"])
meta[1].metric("Habitation mode", payload["habitation_mode"])
meta[2].metric("Shelter mode", payload["shelter_mode"])
meta[3].metric("Records", f"{len(habitations_raw)} + {len(shelters_raw)}")

if payload["habitation_mode"] in {"LIVE", "CACHED"}:
    render_data_mode_indicator(payload["habitation_mode"])
else:
    st.warning("Habitation provenance is not fully LIVE/CACHED. Do not present it as authoritative until verified.")

feed_status = st.session_state.get("operational_feed_status")
if feed_status:
    with st.expander("Configured feed provenance", expanded=False):
        st.json(feed_status)

st.markdown("### Calibrated hazard layer")
hazard_upload = st.file_uploader(
    "Hazard polygons GeoJSON",
    type=["geojson", "json"],
    key="ops_hazard_geojson",
    help="Each feature must have numeric `hazard_score` from 0–100. Upload only after the class-to-score mapping is documented/approved.",
)
if hazard_upload is not None:
    try:
        hazard_text = hazard_upload.getvalue().decode("utf-8")
        checked = validate_geojson_hazard(hazard_text)
        st.success(f"Hazard GeoJSON valid: {checked['feature_count']} feature(s).")
        confirmed = st.checkbox("I confirm this layer's hazard_score mapping is documented and suitable for analytical use", value=False)
        if st.button("Activate calibrated hazard layer", disabled=not confirmed, width="stretch"):
            st.session_state["operational_hazard_geojson"] = hazard_text
            st.session_state["operational_hazard_name"] = hazard_upload.name
            st.success("Calibrated hazard layer activated. Use Stored/GIS mode on analytical pages.")
    except Exception as exc:
        st.error(f"Hazard layer rejected: {exc}")

if st.session_state.get("operational_hazard_geojson"):
    st.caption(f"Active hazard layer: **{st.session_state.get('operational_hazard_name', 'uploaded GeoJSON')}**")
    if st.button("Remove active hazard layer"):
        st.session_state.pop("operational_hazard_geojson", None)
        st.session_state.pop("operational_hazard_name", None)
        st.rerun()

hazard_profile = st.selectbox("Analytical hazard profile", ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"], index=0, format_func=lambda value: "Stored / calibrated GIS" if value == "stored" else value.title())

try:
    hazard_data = None
    if hazard_profile == "stored" and st.session_state.get("operational_hazard_geojson"):
        hazard_data = geojson_to_gdf(st.session_state["operational_hazard_geojson"])
    habitations = enrich_habitations(habitations_raw, hazard_data=hazard_data, hazard_type=hazard_profile, add_coordination_zones=False)
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
except Exception as exc:
    st.error(f"Operational analysis could not run: {exc}")
    st.caption("Stored/GIS mode needs either an activated calibrated GeoJSON layer or a stored hazard_score in every habitation row.")
    render_disclaimer()
    st.stop()

render_kpi_strip([
    ("Habitations", f"{summary['habitations_monitored']:,}", "Operational records"),
    ("Critical", f"{summary['critical_red_zones']:,}", "Deterministic classification"),
    ("Population at Risk", f"{summary['population_at_risk']:,}", "HIGH + CRITICAL"),
    ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", "Decision-support priority"),
    ("Available Capacity", f"{int(summary['available_shelter_capacity']):,}", "After resource constraints"),
])

st.markdown("### Priority register")
cols = [c for c in ["name", "population", "hazard_score", "risk_score", "risk_level", "relocation_priority", "risk_drivers"] if c in habitations.columns]
st.dataframe(habitations[cols].sort_values("risk_score", ascending=False), width="stretch", hide_index=True)

st.markdown("### Live context at operational geography")
center = payload["center"]
if st.button("Refresh live context at operational area", width="stretch"):
    with st.spinner("Refreshing current weather, air quality and nearby event sources..."):
        st.session_state["ops_workspace_live_snapshot"] = fetch_operations_snapshot(payload["label"], latitude=float(center["latitude"]), longitude=float(center["longitude"]), days=7, radius_km=300, min_magnitude=2.5)

snapshot = st.session_state.get("ops_workspace_live_snapshot")
if snapshot:
    health = pd.DataFrame(snapshot.get("source_health", []))
    if not health.empty:
        st.dataframe(health.astype(str), width="stretch", hide_index=True)
    st.caption("Live observations remain corroborating evidence only. They do not silently mutate H/E/V/A.")

with st.expander("What to provide when I cannot fetch an official source", expanded=False):
    st.markdown("""
Send the source URL and, if possible, one sample/download:
- habitation/population/vulnerability CSV or XLSX;
- shelter/site CSV with capacity, occupancy, water, sanitation, access and safety fields;
- GeoJSON/Shapefile/GeoTIFF or WMS/WFS/ArcGIS REST details for hazard layers;
- API documentation plus a sample JSON/XML response;
- official data.gov.in, Bhuvan, SDMA/district, IMD, CWC, GSI or other accountable-source link.

If access requires login, token or IP whitelisting, do **not** paste the secret in chat. Provide the public schema/docs and configure credentials in deployment secrets.
""")

if st.button("Clear operational workspace", type="secondary"):
    for key in ["operational_workspace", "operational_habitation_assessment", "operational_shelter_assessment", "operational_feed_status", "ops_workspace_live_snapshot", "operational_hazard_geojson", "operational_hazard_name"]:
        st.session_state.pop(key, None)
    st.rerun()

render_disclaimer()
