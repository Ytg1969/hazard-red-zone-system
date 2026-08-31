import folium
import streamlit as st
from streamlit_folium import st_folium

from src.pipeline import enrich_habitations, load_demo_data, load_demo_hazards
from src.ui_theme import (
    RISK_COLORS,
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(page_title="Red Zone Map", layout="wide")
inject_global_css()
render_page_header("Red Zone Map", "Spatial multi-hazard view across realistic Indian demo geographies. Hazard footprints remain synthetic DEMO geometries.")
render_data_mode_indicator("DEMO")
city, hazard_profile = render_demo_scope_controls("map")

try:
    habitations_raw, _ = load_demo_data(city)
    hazards = load_demo_hazards()
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type=hazard_profile)
except Exception as exc:
    st.error(f"Unable to load the demonstration map: {exc}")
    render_disclaimer()
    st.stop()

with st.sidebar:
    st.subheader("Map Filters")
    risk_levels = st.multiselect("Risk levels", ["CRITICAL", "HIGH", "MODERATE", "LOW"], default=["CRITICAL", "HIGH", "MODERATE", "LOW"])
    show_population = st.checkbox("Scale markers by population", value=True)
    show_hazards = st.checkbox("Show synthetic hazard footprints", value=True)
    show_zones = st.checkbox("Show coordination zone in popups", value=True)

filtered = habitations[habitations["risk_level"].isin(risk_levels)].copy()
if filtered.empty:
    st.info("No habitations match the selected map filters.")
    render_disclaimer()
    st.stop()

selected_name = st.selectbox("Inspect habitation", filtered.sort_values("risk_score", ascending=False)["name"].tolist())
selected = filtered[filtered["name"] == selected_name].iloc[0]
map_center = [float(filtered["latitude"].mean()), float(filtered["longitude"].mean())]
map_obj = folium.Map(location=map_center, zoom_start=10 if city != "All Demo Cities" else 5, tiles="OpenStreetMap", control_scale=True)

if show_hazards:
    visible_hazards = hazards
    if city != "All Demo Cities" and "demo_city" in hazards.columns:
        visible_hazards = hazards[hazards["demo_city"] == city]
    def hazard_style(feature):
        score = float(feature["properties"].get("hazard_score", 0))
        color = "#dc3545" if score >= 80 else "#ea8600" if score >= 60 else "#f9ab00" if score >= 40 else "#34a853"
        return {"fillColor": color, "color": color, "weight": 2, "fillOpacity": 0.16}
    if not visible_hazards.empty:
        folium.GeoJson(
            visible_hazards.__geo_interface__, name="Synthetic Demo Hazard Footprints", style_function=hazard_style,
            tooltip=folium.GeoJsonTooltip(fields=["name", "hazard_type", "hazard_score", "data_mode"], aliases=["Zone", "Hazard", "Score", "Mode"], sticky=False),
        ).add_to(map_obj)

for row in filtered.to_dict(orient="records"):
    radius = max(6, min(18, 5 + float(row["population"]) / 350)) if show_population else 8
    color = RISK_COLORS.get(row["risk_level"], "#6c757d")
    zone_text = f"<br>Coordination: {row.get('coordination_zone','—')}" if show_zones else ""
    popup = f"<b>{row['name']}</b><br>City: {row.get('demo_city','—')}<br>Risk: {row['risk_score']:.1f} / {row['risk_level']}<br>Hazard profile: {row.get('hazard_profile','stored')}<br>Population: {int(row['population']):,}<br>Priority: {row['relocation_priority']}{zone_text}"
    folium.CircleMarker(location=[row["latitude"], row["longitude"]], radius=radius, popup=folium.Popup(popup, max_width=300), tooltip=f"{row['name']} — {row['risk_level']}", color=color, fill=True, fill_color=color, fill_opacity=0.82, weight=2).add_to(map_obj)

folium.LayerControl(collapsed=True).add_to(map_obj)
left, right = st.columns([2.2, 1], gap="large")
with left:
    st_folium(map_obj, height=620, width=1000, returned_objects=[])
    st.caption("The city locations are real geographies. Bundled hazard footprints and operational values are synthetic DEMO scenario inputs; they are not official hazard-zone boundaries.")
with right:
    st.subheader(selected["name"])
    render_risk_badge(selected["risk_level"])
    st.metric("Risk Score", f"{selected['risk_score']:.1f}/100")
    st.metric("Hazard Score", f"{selected['hazard_score']:.1f}/100")
    st.metric("Population", f"{int(selected['population']):,}")
    st.metric("Relocation Priority", selected["relocation_priority"])
    st.metric("Hazard Data Completeness", f"{float(selected.get('hazard_data_completeness',0)):.0f}%")
    st.write(f"**Primary drivers:** {selected['risk_drivers']}")
    st.write(f"**Coordination zone:** {selected.get('coordination_zone','—')} (experimental grouping only)")
    st.code(f"{selected['latitude']:.5f}, {selected['longitude']:.5f}")

st.markdown("**Risk legend:** CRITICAL = red · HIGH = orange · MODERATE = amber · LOW = green")
render_disclaimer()
