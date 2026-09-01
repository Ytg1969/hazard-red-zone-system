import os
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.bhuvan_layers import layers_for_city
from src.operational_hazards import geojson_to_gdf
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.relocation import rank_shelters
from src.routing import estimate_route
from src.ui_theme import RISK_COLORS, inject_global_css, render_data_mode_indicator, render_demo_scope_controls, render_disclaimer, render_page_header, render_risk_badge

ROAD_GRAPH_FILES = {
    "Puri": Path("data/cache/roads/Puri_Odisha_India.graphml"),
    "Guwahati": Path("data/cache/roads/Guwahati_Assam_India.graphml"),
    "Chennai": Path("data/cache/roads/Chennai_Tamil_Nadu_India.graphml"),
}


def _red_zone_radius_m(risk_score: float) -> float:
    score = max(50.0, min(100.0, float(risk_score)))
    return 650.0 + (score - 50.0) * 24.0


st.set_page_config(page_title="Red Zone Map", layout="wide")
inject_global_css()
render_page_header("Red Zone Map", "Operational map for red-zone inspection, calibrated GIS exposure and capacity-safe shelter routing.")

workspace = st.session_state.get("operational_workspace")
operational = bool(workspace)
selected_bhuvan = None

if operational:
    mode = workspace.get("habitation_mode", "UNVERIFIED")
    render_data_mode_indicator(mode if mode in {"LIVE", "CACHED", "DEMO"} else "DEMO")
    area_label = workspace.get("label", "Operational area")
    hazard_profile = st.sidebar.selectbox("Analytical hazard profile", ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"], index=0, format_func=lambda v: "Stored / calibrated GIS" if v == "stored" else v.title())
    habitations_raw = pd.DataFrame(workspace["habitations"])
    shelters_raw = pd.DataFrame(workspace["shelters"])
    hazard_data = None
    if hazard_profile == "stored" and st.session_state.get("operational_hazard_geojson"):
        try:
            hazard_data = geojson_to_gdf(st.session_state["operational_hazard_geojson"])
        except Exception as exc:
            st.error(f"Active operational hazard layer could not be loaded: {exc}")
            st.stop()
    st.sidebar.success(f"Operational workspace: {area_label}")
    st.sidebar.page_link("pages/9_Operational_Data.py", label="Manage operational data")
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("map")
    area_label = city
    habitations_raw, shelters_raw = load_demo_data(city)
    hazard_data = load_demo_hazards()

try:
    habitations = enrich_habitations(habitations_raw, hazard_data=hazard_data, hazard_type=hazard_profile, add_coordination_zones=not operational)
    shelters = enrich_shelters(shelters_raw)
except Exception as exc:
    st.error(f"Unable to prepare red-zone map: {exc}")
    render_disclaimer()
    st.stop()

with st.sidebar:
    st.subheader("Map filters")
    risk_levels = st.multiselect("Risk levels", ["CRITICAL", "HIGH", "MODERATE", "LOW"], default=["CRITICAL", "HIGH", "MODERATE", "LOW"])
    show_population = st.checkbox("Scale markers by population", value=True)
    show_red_zones = st.checkbox("Show HIGH / CRITICAL decision zones", value=True)
    show_shelters = st.checkbox("Show safe shelter candidates", value=True)
    show_route = st.checkbox("Show selected shelter route", value=True)
    allow_live_route = st.checkbox("Use live road routing when cache is missing", value=True)

    if not operational:
        bhuvan_options = layers_for_city(city)
        if bhuvan_options:
            st.subheader("Authoritative GIS context")
            if st.checkbox("Show Bhuvan WMS overlay", value=False):
                labels = [item["label"] for item in bhuvan_options]
                chosen = st.selectbox("Bhuvan layer", labels)
                selected_bhuvan = next(item for item in bhuvan_options if item["label"] == chosen)
                st.caption("Context only; this WMS is not a calibrated numerical input.")

filtered = habitations[habitations["risk_level"].isin(risk_levels)].copy()
if filtered.empty:
    st.info("No habitations match the selected filters.")
    st.stop()

head_left, head_right = st.columns([2.2, 1])
with head_left:
    selected_name = st.selectbox("Inspect habitation", filtered.sort_values("risk_score", ascending=False)["name"].tolist())
with head_right:
    st.caption("Active scope")
    st.markdown(f"**{area_label}** · {hazard_profile.replace('_', ' ').title()}")

selected = filtered[filtered["name"] == selected_name].iloc[0]
local_shelters = shelters
if not operational and selected.get("demo_city") and "demo_city" in shelters.columns:
    local_shelters = shelters[shelters["demo_city"] == selected["demo_city"]].copy()
ranked_shelters = rank_shelters(selected.to_dict(), local_shelters)

selected_shelter_name = None
if ranked_shelters:
    labels = [f"{i+1}. {s['shelter_name']} · suitability {s['suitability_score']:.1f}" for i, s in enumerate(ranked_shelters)]
    chosen = st.selectbox("Route to safe shelter", labels)
    selected_shelter_name = ranked_shelters[labels.index(chosen)]["shelter_name"]

summary = st.columns(4)
summary[0].metric("Risk", f"{selected['risk_score']:.1f}/100")
summary[1].metric("Population", f"{int(selected['population']):,}")
summary[2].metric("Priority", selected["relocation_priority"])
summary[3].metric("Safe candidates", len(ranked_shelters))

if operational and hazard_data is None and hazard_profile == "stored":
    st.info("No calibrated GeoJSON is active; this view is using the stored hazard_score supplied with the operational habitation dataset.")
elif operational and hazard_data is not None:
    st.success(f"Calibrated operational hazard layer active: {st.session_state.get('operational_hazard_name', 'GeoJSON')}")

map_center = [float(filtered["latitude"].mean()), float(filtered["longitude"].mean())]
map_obj = folium.Map(location=map_center, zoom_start=10 if len(filtered) < 80 else 8, tiles=None, control_scale=True)
folium.TileLayer(tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", attr="© OpenStreetMap contributors", name="OpenStreetMap", overlay=False, control=False, max_zoom=19).add_to(map_obj)

if selected_bhuvan:
    folium.WmsTileLayer(url=selected_bhuvan["service_url"], layers=selected_bhuvan["layer"], name=f"Bhuvan — {selected_bhuvan['label']}", fmt="image/png", transparent=True, overlay=True, control=True, show=True, version="1.1.1", attr="NRSC/ISRO Bhuvan").add_to(map_obj)

if show_red_zones:
    for row in filtered[filtered["risk_level"].isin(["HIGH", "CRITICAL"])].to_dict(orient="records"):
        color = RISK_COLORS.get(row["risk_level"], "#dc3545")
        folium.Circle(
            [float(row["latitude"]), float(row["longitude"])],
            radius=_red_zone_radius_m(row["risk_score"]), color=color, weight=3 if row["name"] == selected_name else 2,
            fill=True, fill_color=color, fill_opacity=.14 if row["name"] == selected_name else .09,
            tooltip=f"{row['name']} · {row['risk_level']} · {row['risk_score']:.1f}/100",
        ).add_to(map_obj)

for row in filtered.to_dict(orient="records"):
    radius = max(6, min(18, 5 + float(row["population"]) / 350)) if show_population else 8
    color = RISK_COLORS.get(row["risk_level"], "#6c757d")
    popup = f"<b>{row['name']}</b><br>Risk: {row['risk_score']:.1f} / {row['risk_level']}<br>Hazard: {row.get('hazard_score', 0):.1f}<br>Population: {int(row['population']):,}<br>Priority: {row['relocation_priority']}"
    folium.CircleMarker([row["latitude"], row["longitude"]], radius=radius, popup=folium.Popup(popup, max_width=320), tooltip=f"{row['name']} — {row['risk_level']}", color="#111827" if row["name"] == selected_name else "#ffffff", fill=True, fill_color=color, fill_opacity=.96, weight=4 if row["name"] == selected_name else 2).add_to(map_obj)

if show_shelters:
    for i, shelter in enumerate(ranked_shelters):
        target = shelter["shelter_name"] == selected_shelter_name
        folium.Marker([float(shelter["latitude"]), float(shelter["longitude"])], tooltip=f"Safe shelter #{i+1}: {shelter['shelter_name']}", popup=folium.Popup(f"<b>{shelter['shelter_name']}</b><br>Safety: {shelter['safety_score']:.0f}/100<br>Available: {int(shelter['available_capacity']):,}<br>Suitability: {shelter['suitability_score']:.1f}/100", max_width=320), icon=folium.Icon(color="green" if target else "lightgreen", icon="home")).add_to(map_obj)

route = None
recommended = next((s for s in ranked_shelters if s["shelter_name"] == selected_shelter_name), ranked_shelters[0] if ranked_shelters else None)
if show_route and recommended:
    origin = (float(selected["latitude"]), float(selected["longitude"]))
    destination = (float(recommended["latitude"]), float(recommended["longitude"]))
    graph_path = None
    if operational:
        configured_graph = os.getenv("SIH_ROAD_GRAPHML")
        if configured_graph and Path(configured_graph).exists():
            graph_path = Path(configured_graph)
    else:
        candidate = ROAD_GRAPH_FILES.get(str(selected.get("demo_city") or area_label))
        if candidate and candidate.exists():
            graph_path = candidate
    route = estimate_route(origin, destination, graphml_path=graph_path, allow_live_osrm=allow_live_route)
    geometry = route.get("route_geometry") or [list(origin), list(destination)]
    road_mode = route.get("routing_mode") in {"cached_osm_graph", "osrm_live", "osrm_cached"}
    if road_mode:
        folium.PolyLine(geometry, color="#ffffff", weight=10, opacity=.75).add_to(map_obj)
        folium.PolyLine(geometry, color="#1565c0", weight=6, opacity=.98, tooltip="Safe-shelter road route").add_to(map_obj)
    else:
        folium.PolyLine(geometry, color="#5f6368", weight=3, dash_array="10,10", tooltip="Straight-line fallback").add_to(map_obj)
    folium.Marker(list(origin), tooltip=f"Origin: {selected['name']}", icon=folium.Icon(color="red", icon="warning-sign")).add_to(map_obj)
    map_obj.fit_bounds([list(origin), list(destination)], padding=(70, 70))

folium.LayerControl(collapsed=True).add_to(map_obj)
left, right = st.columns([2.15, 1], gap="large")
with left:
    st_folium(map_obj, height=680, width=1100, returned_objects=[])
    st.caption("HIGH/CRITICAL circles are decision-support visualization areas, not statutory hazard boundaries. Route provenance is shown explicitly.")
with right:
    st.markdown("### Selected profile")
    st.subheader(selected["name"])
    render_risk_badge(selected["risk_level"])
    st.metric("Hazard Score", f"{selected['hazard_score']:.1f}/100")
    st.write(f"**Drivers:** {selected['risk_drivers']}")
    st.markdown("### Safe shelter candidates")
    if ranked_shelters:
        for i, shelter in enumerate(ranked_shelters[:8]):
            marker = "→" if shelter["shelter_name"] == selected_shelter_name else "•"
            st.write(f"{marker} **#{i+1} {shelter['shelter_name']}** · capacity {int(shelter['available_capacity']):,} · suitability {shelter['suitability_score']:.1f}")
    else:
        st.warning("No shelter passes safety and capacity gates.")
    if route and recommended:
        st.markdown("### Route")
        st.success(f"{selected['name']} → {recommended['shelter_name']}")
        st.write(f"**{route['distance_km']:.2f} km** · `{route.get('routing_mode')}`")
        if route.get("travel_time_min") is not None:
            st.write(f"Estimated travel time: **{route['travel_time_min']:.1f} min**")

render_disclaimer()
