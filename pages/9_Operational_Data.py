import pandas as pd
import streamlit as st

from src.live_operations import fetch_operations_snapshot
from src.operational_workspace import (
    normalize_operational_habitations,
    normalize_operational_shelters,
    serialize_workspace,
)
from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_kpi_strip, render_page_header

st.set_page_config(page_title="Operational Data", page_icon="DATA", layout="wide")
inject_global_css()
render_page_header(
    "Operational Data Workspace",
    "Load authoritative or field-validated habitation and relocation-site datasets, inspect provenance, run the deterministic pipeline, and query live context at the uploaded geography.",
)

st.info(
    "Use this page to replace bundled demonstration inputs with real operational records. The app validates structure and consistency, but source authenticity must still be confirmed by the responsible authority."
)

left, right = st.columns(2, gap="large")
with left:
    habitation_upload = st.file_uploader("Habitation / settlement CSV", type=["csv"], key="ops_hab")
with right:
    shelter_upload = st.file_uploader("Shelter / relocation-site CSV", type=["csv"], key="ops_shelter")
label = st.text_input("Operational area label", placeholder="e.g. Wayanad District, Kerala")

activate = st.button("Validate and activate operational workspace", type="primary", width="stretch", disabled=not (habitation_upload and shelter_upload))

if activate:
    try:
        habitations_raw, h_assessment = normalize_operational_habitations(pd.read_csv(habitation_upload))
        shelters_raw, s_assessment = normalize_operational_shelters(pd.read_csv(shelter_upload))
        payload = serialize_workspace(habitations_raw, shelters_raw, label=label or "Operational upload")
        st.session_state["operational_workspace"] = payload
        st.session_state["operational_habitation_assessment"] = h_assessment
        st.session_state["operational_shelter_assessment"] = s_assessment
        st.success("Operational workspace activated for this browser session.")
    except Exception as exc:
        st.error(f"Could not activate operational data: {exc}")

payload = st.session_state.get("operational_workspace")
if not payload:
    st.warning("No operational workspace is active yet. Upload both validated datasets to continue.")
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

hazard_profile = st.selectbox(
    "Analytical hazard profile",
    ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
    index=0,
    format_func=lambda value: value.title(),
)

try:
    habitations = enrich_habitations(habitations_raw, hazard_type=hazard_profile, add_coordination_zones=False)
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
except Exception as exc:
    st.error(f"Operational analysis could not run: {exc}")
    st.caption("For a real dataset, use Stored/GIS score unless the uploaded rows contain the indicator fields required by the selected prototype hazard profile.")
    render_disclaimer()
    st.stop()

render_kpi_strip([
    ("Habitations", f"{summary['habitations_monitored']:,}", "Uploaded operational records"),
    ("Critical", f"{summary['critical_red_zones']:,}", "Deterministic classification"),
    ("Population at Risk", f"{summary['population_at_risk']:,}", "HIGH + CRITICAL"),
    ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", "Decision-support priority"),
    ("Available Capacity", f"{int(summary['available_shelter_capacity']):,}", "After resource constraints"),
])

st.markdown("### Priority register")
cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"] if c in habitations.columns]
st.dataframe(habitations[cols].sort_values("risk_score", ascending=False), width="stretch", hide_index=True)

st.markdown("### Live context at operational geography")
center = payload["center"]
if st.button("Refresh live context at uploaded area", width="stretch"):
    with st.spinner("Refreshing current weather, air quality and nearby event sources..."):
        st.session_state["ops_workspace_live_snapshot"] = fetch_operations_snapshot(
            payload["label"],
            latitude=float(center["latitude"]),
            longitude=float(center["longitude"]),
            days=7,
            radius_km=300,
            min_magnitude=2.5,
        )

snapshot = st.session_state.get("ops_workspace_live_snapshot")
if snapshot:
    health = pd.DataFrame(snapshot.get("source_health", []))
    if not health.empty:
        st.dataframe(health.astype(str), width="stretch", hide_index=True)
    st.caption("This live context remains corroborating evidence only and does not silently alter the frozen risk score.")

with st.expander("What to provide when a source cannot be fetched", expanded=False):
    st.markdown(
        """
        Provide any one of these, preferably with source URL and update date:

        - CSV/XLSX export of settlement or shelter records.
        - GeoJSON/Shapefile export of hazard boundaries.
        - Official WMS/WFS/ArcGIS REST endpoint and exact layer name.
        - API documentation plus a sample response.
        - A public download URL from data.gov.in, Bhuvan, a State SDMA, district portal, IMD, CWC, GSI or another accountable authority.

        Do not send passwords or private API credentials in chat. For authenticated services, configure credentials in deployment secrets and provide only the endpoint/schema documentation here.
        """
    )

render_disclaimer()
