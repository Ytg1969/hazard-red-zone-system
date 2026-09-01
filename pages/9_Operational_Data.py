import pandas as pd
import streamlit as st

from src.live_operations import fetch_operations_snapshot
from src.operational_sources import (
    configured_operational_urls,
    fetch_operational_habitations,
    fetch_operational_shelters,
)
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
    "Load authority/field datasets manually or from configured HTTPS feeds, run the deterministic relocation pipeline, and query live context at the operational geography.",
)

st.info(
    "This is the transition path away from bundled demo cities. A reachable feed is not automatically authoritative: source ownership, update time and field definitions must still be verified."
)

source_mode = st.segmented_control("Data source", ["Upload files", "Configured HTTPS feeds"], default="Upload files")
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
            payload = serialize_workspace(habitations_raw, shelters_raw, label=label or "Operational upload")
            st.session_state["operational_workspace"] = payload
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
    refresh_feeds = st.button(
        "Fetch, validate and activate configured feeds",
        type="primary",
        width="stretch",
        disabled=not (configured["habitations"] and configured["shelters"]),
    )
    if refresh_feeds:
        try:
            with st.spinner("Fetching configured operational datasets..."):
                h_result = fetch_operational_habitations()
                s_result = fetch_operational_shelters()
            payload = serialize_workspace(h_result["data"], s_result["data"], label=label or "Configured operational feeds")
            st.session_state["operational_workspace"] = payload
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
    st.caption("For a real dataset, use Stored/GIS score unless the rows contain the indicators required by the selected prototype hazard profile.")
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
cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"] if c in habitations.columns]
st.dataframe(habitations[cols].sort_values("risk_score", ascending=False), width="stretch", hide_index=True)

st.markdown("### Live context at operational geography")
center = payload["center"]
if st.button("Refresh live context at operational area", width="stretch"):
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

with st.expander("What to provide when I cannot fetch an official source", expanded=False):
    st.markdown(
        """
        Send the source URL and, if possible, one sample/download. The most useful inputs are:

        - CSV export of habitation/population/vulnerability records.
        - CSV export of shelters/relocation sites with capacity, occupancy, water, sanitation and access fields.
        - GeoJSON/Shapefile or WMS/WFS/ArcGIS REST details for hazard boundaries.
        - API documentation plus a sample JSON/XML response.
        - data.gov.in resource link, Bhuvan layer/service name, State SDMA/district download, IMD/CWC/GSI source page, or another accountable authority source.

        For a source that needs login, IP whitelist or token, do **not** paste the secret into chat. Give me the public documentation/schema and configure the credential later in deployment secrets.
        """
    )

render_disclaimer()
