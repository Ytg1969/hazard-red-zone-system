import pandas as pd
import streamlit as st

from src.ogc_sources import inspect_wms_source
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_page_header

st.set_page_config(page_title="GIS Source Inspector", page_icon="GIS", layout="wide")
inject_global_css()
render_page_header(
    "GIS Source Inspector",
    "Inspect authority WMS services, discover exact layer names and preserve provenance before any hazard layer is allowed into analytical scoring.",
)

st.info(
    "Use this for Bhuvan, SDMA, district, or other accountable OGC Web Map Services. "
    "A reachable WMS layer is context only; it does not become H until its legend/classes, reference period, CRS and class-to-0–100 mapping are documented and reviewed."
)

with st.container(border=True):
    st.markdown("### Inspect a WMS service")
    wms_url = st.text_input(
        "WMS service URL",
        placeholder="https://agency.example.gov.in/geoserver/workspace/wms",
        help="HTTPS only. Existing vendor query parameters are preserved while GetCapabilities is requested.",
    )
    inspect = st.button("Fetch capabilities", type="primary", width="stretch", disabled=not wms_url.strip())

if inspect:
    try:
        with st.spinner("Fetching WMS capabilities..."):
            st.session_state["wms_inspection"] = inspect_wms_source(wms_url.strip())
    except Exception as exc:
        st.session_state.pop("wms_inspection", None)
        st.error(f"WMS inspection failed: {exc}")

result = st.session_state.get("wms_inspection")
if result:
    meta = st.columns(5)
    meta[0].metric("Service", result.get("service_title") or "WMS")
    meta[1].metric("Version", result.get("version") or "Unknown")
    meta[2].metric("Named layers", int(result.get("layer_count") or 0))
    meta[3].metric("Mode", result.get("mode") or "Unknown")
    meta[4].metric("Stale", "Yes" if result.get("stale") else "No")
    if result.get("mode") in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(result["mode"])

    st.caption(f"Capabilities URL: `{result.get('source_url')}`")
    if result.get("service_abstract"):
        st.write(result["service_abstract"])

    layers = pd.DataFrame(result.get("layers", []))
    if not layers.empty:
        layers["crs"] = layers["crs"].apply(lambda values: ", ".join(values) if isinstance(values, list) else str(values))
        layers["geographic_bbox"] = layers["geographic_bbox"].astype(str)
        search = st.text_input("Filter layers", placeholder="flood, landslide, erosion, susceptibility...")
        shown = layers
        if search.strip():
            needle = search.strip().lower()
            mask = layers.astype(str).apply(lambda col: col.str.lower().str.contains(needle, regex=False)).any(axis=1)
            shown = layers[mask]
        st.dataframe(shown, width="stretch", hide_index=True)

        names = shown["name"].astype(str).tolist()
        if names:
            selected = st.selectbox("Selected layer", names)
            row = shown.loc[shown["name"].astype(str) == selected].iloc[0]
            st.markdown("### Integration evidence checklist")
            c1, c2 = st.columns(2)
            with c1:
                st.write(f"**Layer name:** `{selected}`")
                st.write(f"**Title:** {row.get('title')}")
                st.write(f"**Advertised CRS:** {row.get('crs') or 'Not stated'}")
            with c2:
                st.write("Before analytical use, obtain:")
                st.write("- source owner / publication page")
                st.write("- reference period / update timestamp")
                st.write("- legend or hazard class definitions")
                st.write("- documented class → 0–100 mapping")
                st.write("- geographic coverage and limitations")

            st.warning(
                "This inspector intentionally does not activate the selected layer as a risk input. "
                "Once the mapping is documented, export/convert the calibrated geometry to the operational GeoJSON contract or add a source-specific calibrated adapter."
            )

st.markdown("### Current government-source blockers")
blockers = pd.DataFrame([
    {"Source": "IMD", "Status": "Authorization dependent", "What is needed": "Approved API endpoints + auth method + redacted sample response"},
    {"Source": "NDMA SACHET", "Status": "Portal verified; feed mapping pending", "What is needed": "Verified RSS/CAP identifier/feed URL or representative feed sample"},
    {"Source": "Shelter inventories", "Status": "No single national live capacity feed verified", "What is needed": "State/district CSV/XLSX/API with coordinates + capacity/occupancy/infrastructure"},
    {"Source": "Hazard WMS", "Status": "Discoverable", "What is needed": "Exact layer + legend/classes + reference period + calibrated mapping"},
])
st.dataframe(blockers, width="stretch", hide_index=True)

render_disclaimer()
