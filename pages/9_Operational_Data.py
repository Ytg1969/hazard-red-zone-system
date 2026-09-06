import pandas as pd
import streamlit as st

from src.operational_file_ingest import read_operational_upload
from src.operational_hazards import configured_hazard_source, geojson_to_gdf, validate_geojson_hazard
from src.operational_sources import configured_operational_urls, fetch_operational_habitations, fetch_operational_shelters
from src.operational_workspace import normalize_operational_habitations, normalize_operational_shelters, serialize_workspace
from src.pipeline import calculate_summary, enrich_habitations, enrich_shelters
from src.runtime_mode import offline_mode
from src.streamlit_workspace import resolve_operational_hazard, resolve_operational_workspace
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_kpi_strip, render_page_header

st.set_page_config(page_title="Operational Data", page_icon="DATA", layout="wide", initial_sidebar_state="auto")
inject_global_css()
render_page_header(
    "Operational Data",
    "Load, validate and activate habitation, relocation-site and calibrated hazard evidence for the operator workflow.",
)

offline = offline_mode()
if offline:
    st.info("Offline field mode is active. Local file uploads and active browser-session data remain available; remote HTTPS source actions are disabled.")
else:
    st.caption("A reachable source is not automatically authoritative. Ownership, timestamps, field definitions and hazard calibration remain explicit validation requirements.")

# This management page deliberately bypasses the strict-mode stop so operators
# can recover from a broken/missing configured feed by activating validated uploads.
resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True, enforce_required=False)
except Exception as exc:
    st.warning(f"Configured operational feeds could not be auto-loaded: {exc}")

configured = configured_operational_urls()
configured_hazard = configured_hazard_source()

st.markdown("## 1 · Load settlement and relocation-site data")
if resolved:
    payload = resolved["payload"]
    habitations_raw = resolved["habitations"]
    shelters_raw = resolved["shelters"]
    active_cols = st.columns(4)
    active_cols[0].metric("Active area", payload.get("label", "Operational dataset"))
    active_cols[1].metric("Habitations", len(habitations_raw))
    active_cols[2].metric("Relocation sites", len(shelters_raw))
    active_cols[3].metric("Origin", str(resolved.get("origin", "session")).replace("_", " ").title())
    st.success("A validated operational workspace is active. You can replace it below or continue to hazard evidence.")
else:
    st.warning("No operational workspace is active yet. Start with a matched habitation dataset and relocation-site dataset.")

available_sources = ["Upload files", "Current / configured"]
if not offline:
    available_sources.extend(["Use HTTPS URLs", "Refresh configured feeds"])
default_source = "Current / configured" if resolved else "Upload files"
source_mode = st.segmented_control("Data source", available_sources, default=default_source)

if source_mode == "Upload files":
    st.caption("Upload both datasets together. CSV, XLSX, or Point GeoJSON/JSON are accepted; missing required fields are rejected rather than invented.")
    area_label = st.text_input("Operational area label", placeholder="e.g. Wayanad District, Kerala", key="ops_upload_label")
    left, right = st.columns(2, gap="large")
    with left:
        habitation_upload = st.file_uploader(
            "Habitation / settlement dataset",
            type=["csv", "xlsx", "geojson", "json"],
            key="ops_hab",
        )
    with right:
        shelter_upload = st.file_uploader(
            "Shelter / relocation-site dataset",
            type=["csv", "xlsx", "geojson", "json"],
            key="ops_shelter",
        )
    ready = bool(habitation_upload and shelter_upload)
    if st.button("Validate and activate uploaded workspace", type="primary", width="stretch", disabled=not ready):
        try:
            habitations_checked, h_assessment = normalize_operational_habitations(read_operational_upload(habitation_upload))
            shelters_checked, s_assessment = normalize_operational_shelters(read_operational_upload(shelter_upload))
            st.session_state["operational_workspace"] = serialize_workspace(
                habitations_checked,
                shelters_checked,
                label=area_label or "Operational upload",
            )
            st.session_state["operational_habitation_assessment"] = h_assessment
            st.session_state["operational_shelter_assessment"] = s_assessment
            st.success("Uploaded operational workspace activated for this browser session.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not activate uploaded data: {exc}")

elif source_mode == "Use HTTPS URLs" and not offline:
    st.caption("Use public HTTPS CSV or Point GeoJSON/JSON endpoints. Private-network targets and URLs containing embedded credentials are rejected.")
    area_label = st.text_input("Operational area label", placeholder="e.g. Wayanad District, Kerala", key="ops_https_label")
    left, right = st.columns(2, gap="large")
    with left:
        habitation_url = st.text_input("Habitation / settlement HTTPS URL", key="ops_session_habitation_url")
    with right:
        shelter_url = st.text_input("Shelter / relocation-site HTTPS URL", key="ops_session_shelter_url")
    ready = bool(habitation_url.strip() and shelter_url.strip())
    if st.button("Fetch, validate and activate HTTPS workspace", type="primary", width="stretch", disabled=not ready):
        try:
            with st.spinner("Fetching and validating operational sources..."):
                h_result = fetch_operational_habitations(habitation_url.strip())
                s_result = fetch_operational_shelters(shelter_url.strip())
            st.session_state["operational_workspace"] = serialize_workspace(
                h_result["data"],
                s_result["data"],
                label=area_label or "Session HTTPS operational feeds",
            )
            st.session_state["operational_habitation_assessment"] = h_result["assessment"]
            st.session_state["operational_shelter_assessment"] = s_result["assessment"]
            st.session_state["operational_feed_status"] = {
                "habitations": {k: h_result.get(k) for k in ["mode", "stale", "fetched_at", "source_url", "format"]},
                "shelters": {k: s_result.get(k) for k in ["mode", "stale", "fetched_at", "source_url", "format"]},
            }
            st.success("HTTPS operational workspace activated for this browser session.")
            st.rerun()
        except Exception as exc:
            st.error(f"HTTPS operational source activation failed: {exc}")

elif source_mode == "Refresh configured feeds" and not offline:
    area_label = st.text_input("Operational area label", placeholder="Configured operational feeds", key="ops_configured_label")
    configured_ready = bool(configured.get("habitations") and configured.get("shelters"))
    if not configured_ready:
        st.warning("Both configured habitation and relocation-site feeds are required before refresh.")
    if st.button("Refresh and activate configured feeds", type="primary", width="stretch", disabled=not configured_ready):
        try:
            with st.spinner("Fetching configured operational datasets..."):
                h_result = fetch_operational_habitations()
                s_result = fetch_operational_shelters()
            st.session_state["operational_workspace"] = serialize_workspace(
                h_result["data"],
                s_result["data"],
                label=area_label or "Configured operational feeds",
            )
            st.session_state["operational_habitation_assessment"] = h_result["assessment"]
            st.session_state["operational_shelter_assessment"] = s_result["assessment"]
            st.session_state["operational_feed_status"] = {
                "habitations": {k: h_result.get(k) for k in ["mode", "stale", "fetched_at", "source_url", "format"]},
                "shelters": {k: s_result.get(k) for k in ["mode", "stale", "fetched_at", "source_url", "format"]},
            }
            st.success("Configured operational feeds activated.")
            st.rerun()
        except Exception as exc:
            st.error(f"Configured feed refresh failed: {exc}")

else:
    if resolved:
        st.caption("The current validated workspace will remain active until you replace or clear it.")
    elif offline:
        st.info("No browser-session workspace is active. Upload local files to continue while offline.")
    else:
        st.info("No active workspace was resolved. Upload files, use HTTPS URLs, or configure both deployment feeds.")

# Resolve again after any activation action; strict production mode remains
# bypassed only on this management page so the upload/recovery workflow is usable.
try:
    resolved = resolve_operational_workspace(auto_configured=True, enforce_required=False)
except Exception as exc:
    resolved = None
    st.error(f"Operational workspace validation failed: {exc}")

with st.expander("Deployment source settings", expanded=False):
    config_cols = st.columns(3)
    config_cols[0].metric("Habitation feed", "Configured" if configured.get("habitations") else "Not configured")
    config_cols[1].metric("Relocation-site feed", "Configured" if configured.get("shelters") else "Not configured")
    config_cols[2].metric(
        "Calibrated hazard feed",
        "Ready" if configured_hazard.get("url") and configured_hazard.get("calibration_confirmed") else "Not ready",
    )
    st.caption(
        "Deployment variables: SIH_HABITATION_CSV_URL, SIH_SHELTER_CSV_URL, SIH_HAZARD_GEOJSON_URL, "
        "SIH_HAZARD_CALIBRATION_CONFIRMED, and optional SIH_HAZARD_SOURCE_LABEL."
    )

if not resolved:
    st.markdown("### What the two operational datasets must represent")
    explain_left, explain_right = st.columns(2)
    with explain_left:
        st.markdown("**Habitations / settlements**")
        st.write("Population and coordinates plus the exposure/vulnerability/accessibility evidence required by the schema.")
    with explain_right:
        st.markdown("**Relocation sites / shelters**")
        st.write("Coordinates, physical capacity, occupancy and available safety/resource evidence used by the capacity gate.")
    render_disclaimer()
    st.stop()

payload = resolved["payload"]
habitations_raw = resolved["habitations"]
shelters_raw = resolved["shelters"]
mode = payload.get("habitation_mode", "UNVERIFIED")
if mode in {"LIVE", "CACHED", "DEMO"}:
    render_data_mode_indicator(mode)
else:
    st.warning("Habitation provenance is not fully verified. Do not present it as authoritative until source evidence is confirmed.")

feed_status = st.session_state.get("operational_feed_status")
if feed_status:
    with st.expander("Settlement/site feed provenance", expanded=False):
        st.json(feed_status)

st.markdown("## 2 · Confirm hazard evidence")
hazard_resolved = None
try:
    hazard_resolved = resolve_operational_hazard(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured hazard source is unavailable: {exc}")

if hazard_resolved:
    hcols = st.columns(4)
    hcols[0].metric("Hazard source", str(hazard_resolved.get("label", "Calibrated GeoJSON")))
    hcols[1].metric("Origin", str(hazard_resolved.get("origin", "session")).replace("_", " ").title())
    hcols[2].metric("Mode", hazard_resolved.get("mode", "SESSION"))
    hcols[3].metric("Features", hazard_resolved.get("feature_count", "—"))
    if hazard_resolved.get("stale"):
        st.warning("The calibrated hazard source is being served from cache because the latest refresh was unavailable.")
else:
    st.info("No calibrated hazard polygon layer is active. Stored habitation hazard_score values can still be reviewed, but their provenance must be verified separately.")

with st.expander("Add or replace calibrated hazard GeoJSON", expanded=False):
    hazard_upload = st.file_uploader(
        "Calibrated hazard polygons GeoJSON",
        type=["geojson", "json"],
        key="ops_hazard_geojson",
        help="Every feature must contain numeric hazard_score from 0–100. Activate only when the source-specific mapping is documented.",
    )
    if hazard_upload is not None:
        try:
            hazard_text = hazard_upload.getvalue().decode("utf-8")
            checked = validate_geojson_hazard(hazard_text)
            st.success(f"GeoJSON valid: {checked['feature_count']} feature(s).")
            confirmed = st.checkbox("I confirm this source's hazard_score mapping is documented and approved for analytical use", value=False)
            if st.button("Activate uploaded calibrated hazard", disabled=not confirmed, width="stretch"):
                st.session_state["operational_hazard_geojson"] = hazard_text
                st.session_state["operational_hazard_name"] = hazard_upload.name
                st.success("Uploaded calibrated hazard layer activated.")
                st.rerun()
        except Exception as exc:
            st.error(f"Hazard layer rejected: {exc}")

st.markdown("## 3 · Review the operational analysis")
hazard_profile = st.selectbox(
    "Analytical hazard profile",
    ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
    index=0,
    format_func=lambda value: "Stored / calibrated GIS" if value == "stored" else value.title(),
)

try:
    hazard_data = None
    if hazard_profile == "stored" and hazard_resolved:
        hazard_data = geojson_to_gdf(hazard_resolved["geojson"])
    habitations = enrich_habitations(
        habitations_raw,
        hazard_data=hazard_data,
        hazard_type=hazard_profile,
        add_coordination_zones=False,
    )
    shelters = enrich_shelters(shelters_raw)
    summary = calculate_summary(habitations, shelters)
except Exception as exc:
    st.error(f"Operational analysis could not run: {exc}")
    st.caption("Stored/GIS mode requires a verified stored hazard_score or a calibrated GeoJSON hazard layer.")
    render_disclaimer()
    st.stop()

render_kpi_strip([
    ("Habitations", f"{summary['habitations_monitored']:,}", "Operational records"),
    ("Critical", f"{summary['critical_red_zones']:,}", "Deterministic classification"),
    ("Population at Risk", f"{summary['population_at_risk']:,}", "HIGH + CRITICAL"),
    ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", "Decision-support priority"),
    ("Available Capacity", f"{int(summary['available_shelter_capacity']):,}", "After limiting-resource constraints"),
])

priority_cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority", "risk_drivers"] if c in habitations.columns]
with st.expander("Priority register", expanded=False):
    st.dataframe(habitations[priority_cols].sort_values("risk_score", ascending=False), width="stretch", hide_index=True)

st.markdown("## 4 · Continue the operator workflow")
nav = st.columns(4, gap="small")
with nav[0]:
    st.page_link("pages/2_Red_Zone_Map.py", label="Open Red Zone Map", use_container_width=True)
with nav[1]:
    st.page_link("pages/3_Risk_Analysis.py", label="Open Risk Analysis", use_container_width=True)
with nav[2]:
    st.page_link("pages/4_Relocation_Planner.py", label="Open Relocation Planner", use_container_width=True)
with nav[3]:
    st.page_link("pages/7_Live_Data_Context.py", label="Open Live Context", use_container_width=True)
if offline:
    st.caption("Live Context will show explicit OFFLINE source state; the deterministic red-zone and relocation workflow remains local.")
else:
    st.caption("Live Context is deliberately separate so current observations cannot silently mutate the analytical risk inputs.")

with st.expander("Workspace maintenance", expanded=False):
    st.caption("Clearing the browser-session workspace does not delete configured deployment sources.")
    if st.button("Clear browser-session workspace", type="secondary"):
        for key in [
            "operational_workspace",
            "operational_habitation_assessment",
            "operational_shelter_assessment",
            "operational_feed_status",
            "ops_workspace_live_snapshot",
            "operational_hazard_geojson",
            "operational_hazard_name",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

with st.expander("If an official source cannot be fetched", expanded=False):
    st.markdown(
        "Provide the public source URL plus one non-secret sample/download: CSV/XLSX, GeoJSON/Shapefile/GeoTIFF, WMS/WFS/ArcGIS REST layer details, or API docs with a redacted JSON/XML sample. "
        "For login/token/IP-whitelisted services, keep credentials in deployment secrets rather than the UI."
    )

render_disclaimer()
