import pandas as pd
import streamlit as st

from src.arcgis_sources import geojson_query_url, inspect_arcgis_source, layer_url
from src.ogc_sources import inspect_wms_source
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_page_header

st.set_page_config(page_title="GIS Source Inspector", page_icon="GIS", layout="wide")
inject_global_css()
render_page_header(
    "GIS Source Inspector",
    "Discover authority WMS and ArcGIS REST layers while preserving provenance and calibration boundaries.",
)

st.info(
    "Use this for Bhuvan, SDMA, district and other accountable public GIS services. "
    "Reachability alone never makes a layer an analytical risk input: legend/classes, reference period, CRS, coverage and the class-to-0–100 mapping must still be documented."
)

wms_tab, arcgis_tab = st.tabs(["OGC WMS", "ArcGIS REST"])

with wms_tab:
    with st.container(border=True):
        st.markdown("### Inspect a WMS service")
        wms_url = st.text_input(
            "WMS service URL",
            placeholder="https://agency.example.gov.in/geoserver/workspace/wms",
            help="HTTPS only. Existing vendor query parameters are preserved while GetCapabilities is requested.",
            key="gis_wms_url",
        )
        inspect = st.button("Fetch WMS capabilities", type="primary", width="stretch", disabled=not wms_url.strip())

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
            search = st.text_input("Filter WMS layers", placeholder="flood, landslide, erosion, susceptibility...")
            shown = layers
            if search.strip():
                needle = search.strip().lower()
                mask = layers.astype(str).apply(lambda col: col.str.lower().str.contains(needle, regex=False)).any(axis=1)
                shown = layers[mask]
            st.dataframe(shown, width="stretch", hide_index=True)

            names = shown["name"].astype(str).tolist()
            if names:
                selected = st.selectbox("Selected WMS layer", names)
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
                    "The WMS inspector does not activate this layer as H. Once calibration is documented, convert/export the geometry to the calibrated operational GeoJSON contract or add a reviewed source-specific adapter."
                )

with arcgis_tab:
    with st.container(border=True):
        st.markdown("### Inspect an ArcGIS REST service or layer")
        arcgis_url = st.text_input(
            "FeatureServer / MapServer URL",
            placeholder="https://agency.example.gov.in/arcgis/rest/services/Hazards/FeatureServer",
            help="Paste either a service URL or a numbered layer URL. Public HTTPS metadata only.",
            key="gis_arcgis_url",
        )
        arcgis_inspect = st.button("Fetch ArcGIS metadata", type="primary", width="stretch", disabled=not arcgis_url.strip())

    if arcgis_inspect:
        try:
            with st.spinner("Fetching ArcGIS REST metadata..."):
                st.session_state["arcgis_inspection"] = inspect_arcgis_source(arcgis_url.strip())
                st.session_state["arcgis_base_url"] = arcgis_url.strip()
        except Exception as exc:
            st.session_state.pop("arcgis_inspection", None)
            st.error(f"ArcGIS inspection failed: {exc}")

    arcgis = st.session_state.get("arcgis_inspection")
    if arcgis:
        meta = st.columns(5)
        meta[0].metric("Source", arcgis.get("name") or "ArcGIS REST")
        meta[1].metric("Layers", int(arcgis.get("layer_count") or 0))
        meta[2].metric("Fields", int(arcgis.get("field_count") or 0))
        meta[3].metric("Mode", arcgis.get("mode") or "Unknown")
        meta[4].metric("Query", "Yes" if arcgis.get("supports_query") else "No / unknown")
        if arcgis.get("mode") in {"LIVE", "CACHED", "DEMO"}:
            render_data_mode_indicator(arcgis["mode"])

        st.caption(f"Metadata URL: `{arcgis.get('source_url')}`")
        if arcgis.get("description"):
            st.write(arcgis["description"])
        if arcgis.get("geometry_type"):
            st.write(f"**Geometry:** {arcgis.get('geometry_type')}")
        if arcgis.get("extent"):
            st.write(f"**Advertised extent:** `{arcgis.get('extent')}`")

        service_layers = pd.DataFrame(arcgis.get("layers", []))
        if not service_layers.empty:
            st.dataframe(service_layers, width="stretch", hide_index=True)
            ids = service_layers["id"].dropna().tolist()
            if ids:
                selected_id = st.selectbox(
                    "Build layer metadata URL",
                    ids,
                    format_func=lambda value: f"{value} · {service_layers.loc[service_layers['id'] == value, 'name'].iloc[0]}",
                )
                base = st.session_state.get("arcgis_base_url", "")
                if base:
                    selected_layer_url = layer_url(base, selected_id)
                    st.code(selected_layer_url, language=None)
                    st.caption("Inspect this numbered layer URL to see its geometry, fields and Query capability before using a feature export.")

        fields = pd.DataFrame(arcgis.get("fields", []))
        if not fields.empty:
            st.markdown("#### Layer fields")
            st.dataframe(fields, width="stretch", hide_index=True)

        base = st.session_state.get("arcgis_base_url", "")
        if arcgis.get("supports_query") and base and arcgis.get("field_count"):
            st.markdown("#### Public GeoJSON query template")
            st.code(geojson_query_url(base), language=None)
            st.caption(
                "This is only a query template. Confirm licensing, record limits, field meaning and update frequency. A hazard export still needs documented calibration before it can affect H."
            )

        st.markdown("### Integration evidence checklist")
        st.write("- accountable agency / official publication page")
        st.write("- layer/service update timestamp and reference period")
        st.write("- exact field definitions and units")
        st.write("- CRS / spatial reference and coverage")
        st.write("- record limits / pagination requirements")
        st.write("- hazard legend + class → 0–100 mapping if used for analytical H")
        st.warning("ArcGIS discovery is context-only until the evidence above is reviewed. No discovered field or layer is silently inserted into the frozen risk model.")

st.markdown("### Current government-source blockers")
blockers = pd.DataFrame([
    {"Source": "IMD", "Status": "Authorization dependent", "What is needed": "Approved API endpoints + auth method + redacted sample response"},
    {"Source": "NDMA SACHET", "Status": "Portal verified; feed mapping pending", "What is needed": "Verified RSS/CAP identifier/feed URL or representative feed sample"},
    {"Source": "Shelter inventories", "Status": "No single national live capacity feed verified", "What is needed": "State/district CSV/XLSX/GeoJSON/API with coordinates + capacity/occupancy/infrastructure"},
    {"Source": "Hazard GIS", "Status": "WMS + ArcGIS discovery supported", "What is needed": "Exact layer + legend/classes + reference period + calibrated mapping"},
])
st.dataframe(blockers, width="stretch", hide_index=True)

render_disclaimer()
