from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from src.bhuvan_layers import layers_for_city
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.relocation import rank_shelters
from src.routing import estimate_route
from src.ui_theme import (
    RISK_COLORS,
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_page_header,
    render_risk_badge,
)

ROAD_GRAPH_FILES = {
    "Puri": Path("data/cache/roads/Puri_Odisha_India.graphml"),
    "Guwahati": Path("data/cache/roads/Guwahati_Assam_India.graphml"),
    "Chennai": Path("data/cache/roads/Chennai_Tamil_Nadu_India.graphml"),
}


def _red_zone_radius_m(risk_score: float) -> float:
    """Return a restrained DEMO display radius for a HIGH/CRITICAL habitation.

    This circle is a decision-visualization aid around the habitation, not a
    statutory or scientifically calibrated hazard boundary.
    """
    score = max(50.0, min(100.0, float(risk_score)))
    return 650.0 + (score - 50.0) * 24.0


st.set_page_config(page_title="Red Zone Map", layout="wide")
inject_global_css()
render_page_header(
    "Red Zone Map",
    "Operational map for habitation-centered red-zone inspection, verified GIS context and safe-shelter road routing.",
)
render_data_mode_indicator("DEMO")
city, hazard_profile = render_demo_scope_controls("map")

try:
    habitations_raw, shelters_raw = load_demo_data(city)
    hazards = load_demo_hazards()
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type=hazard_profile)
    shelters = enrich_shelters(shelters_raw)
except Exception as exc:
    st.error(f"Unable to load the demonstration map: {exc}")
    render_disclaimer()
    st.stop()

with st.sidebar:
    st.subheader("Map Filters")
    risk_levels = st.multiselect(
        "Risk levels",
        ["CRITICAL", "HIGH", "MODERATE", "LOW"],
        default=["CRITICAL", "HIGH", "MODERATE", "LOW"],
    )
    show_population = st.checkbox("Scale habitation markers by population", value=True)
    show_red_zones = st.checkbox("Show HIGH / CRITICAL red-zone circles", value=True)
    show_zones = st.checkbox("Show coordination zone in popups", value=True)
    show_route = st.checkbox("Show recommended safe-shelter route", value=True)
    allow_live_route = st.checkbox("Use live road routing when cache is missing", value=True)

    bhuvan_options = layers_for_city(city)
    selected_bhuvan = None
    if bhuvan_options:
        st.subheader("Authoritative GIS Context")
        show_bhuvan = st.checkbox("Show Bhuvan WMS overlay", value=False)
        if show_bhuvan:
            labels = [item["label"] for item in bhuvan_options]
            chosen_label = st.selectbox("Bhuvan layer", labels)
            selected_bhuvan = next(item for item in bhuvan_options if item["label"] == chosen_label)
            st.caption("Context only. The source WMS does not change the deterministic risk score.")
    elif city == "All Demo Cities":
        st.caption("Select one city to enable verified Bhuvan overlays.")

filtered = habitations[habitations["risk_level"].isin(risk_levels)].copy()
if filtered.empty:
    st.info("No habitations match the selected map filters.")
    render_disclaimer()
    st.stop()

st.markdown("### Operational map workspace")
control_left, control_right = st.columns([2.1, 1], gap="large")
with control_left:
    selected_name = st.selectbox(
        "Inspect habitation",
        filtered.sort_values("risk_score", ascending=False)["name"].tolist(),
    )
with control_right:
    st.caption("Active analytical profile")
    st.markdown(f"**{hazard_profile.title()}** · {city}")

selected = filtered[filtered["name"] == selected_name].iloc[0]
selected_city = str(selected.get("demo_city") or city)
local_shelters = shelters
if selected.get("demo_city") and "demo_city" in shelters.columns:
    local_shelters = shelters[shelters["demo_city"] == selected["demo_city"]].copy()

ranked_shelters = rank_shelters(selected.to_dict(), local_shelters)
summary_cols = st.columns(4)
summary_cols[0].metric("Risk Score", f"{selected['risk_score']:.1f}/100")
summary_cols[1].metric("Population", f"{int(selected['population']):,}")
summary_cols[2].metric("Relocation Priority", selected["relocation_priority"])
summary_cols[3].metric("Safe Shelter Candidates", f"{len(ranked_shelters)}")

if selected.get("inside_hazard_zone") is True:
    st.warning("Selected habitation intersects the current DEMO analytical hazard footprint. Shelter selection remains safety- and capacity-gated.")
elif selected.get("inside_hazard_zone") is False and selected.get("distance_to_hazard_km") is not None:
    st.info(f"Selected habitation is outside the DEMO analytical hazard footprint; nearest boundary is approximately {float(selected['distance_to_hazard_km']):.2f} km away.")

map_center = [float(filtered["latitude"].mean()), float(filtered["longitude"].mean())]
map_obj = folium.Map(
    location=map_center,
    zoom_start=11 if city != "All Demo Cities" else 5,
    tiles="CartoDB positron",
    control_scale=True,
)

if selected_bhuvan is not None:
    folium.WmsTileLayer(
        url=selected_bhuvan["service_url"],
        layers=selected_bhuvan["layer"],
        name=f"Bhuvan — {selected_bhuvan['label']}",
        fmt="image/png",
        transparent=True,
        overlay=True,
        control=True,
        show=True,
        version="1.1.1",
        attr="NRSC/ISRO Bhuvan",
    ).add_to(map_obj)

# Red zones are now centered on the actual HIGH/CRITICAL habitations instead of
# approximating arbitrary hazard polygons as large circles. This makes the
# operational view interpretable while keeping the underlying analytical GIS
# geometry unchanged.
if show_red_zones:
    decision_zones = filtered[filtered["risk_level"].isin(["HIGH", "CRITICAL"])]
    for row in decision_zones.to_dict(orient="records"):
        color = RISK_COLORS.get(row["risk_level"], "#dc3545")
        radius_m = _red_zone_radius_m(row["risk_score"])
        is_selected = row["name"] == selected_name
        tooltip = (
            f"<b>{row['name']}</b><br>"
            f"Decision class: {row['risk_level']}<br>"
            f"Risk score: {row['risk_score']:.1f}/100<br>"
            f"Population: {int(row['population']):,}<br>"
            "DEMO decision-visualization circle"
        )
        folium.Circle(
            location=[float(row["latitude"]), float(row["longitude"])],
            radius=radius_m,
            color=color,
            weight=4 if is_selected else 2,
            fill=True,
            fill_color=color,
            fill_opacity=0.16 if is_selected else 0.10,
            opacity=0.95,
            tooltip=folium.Tooltip(tooltip, sticky=False),
            name=f"{row['risk_level']} Red Zone — {row['name']}",
        ).add_to(map_obj)

for row in filtered.to_dict(orient="records"):
    radius = max(6, min(18, 5 + float(row["population"]) / 350)) if show_population else 8
    color = RISK_COLORS.get(row["risk_level"], "#6c757d")
    zone_text = f"<br>Coordination: {row.get('coordination_zone','—')}" if show_zones else ""
    popup = (
        f"<b>{row['name']}</b><br>City: {row.get('demo_city','—')}<br>Risk: {row['risk_score']:.1f} / {row['risk_level']}"
        f"<br>Hazard profile: {row.get('hazard_profile','stored')}<br>Population: {int(row['population']):,}"
        f"<br>Priority: {row['relocation_priority']}{zone_text}"
    )
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=radius,
        popup=folium.Popup(popup, max_width=300),
        tooltip=f"{row['name']} — {row['risk_level']}",
        color="#111827" if row["name"] == selected_name else "#ffffff",
        fill=True,
        fill_color=color,
        fill_opacity=0.96,
        weight=4 if row["name"] == selected_name else 2,
    ).add_to(map_obj)

recommended = ranked_shelters[0] if ranked_shelters else None
route = None
if show_route and recommended:
    origin = (float(selected["latitude"]), float(selected["longitude"]))
    destination = (float(recommended["latitude"]), float(recommended["longitude"]))
    graph_path = ROAD_GRAPH_FILES.get(selected_city)
    route = estimate_route(
        origin,
        destination,
        graphml_path=graph_path if graph_path and graph_path.exists() else None,
        allow_live_osrm=allow_live_route,
    )
    geometry = route.get("route_geometry") or [list(origin), list(destination)]

    folium.Marker(
        list(origin),
        tooltip=f"Red-zone origin: {selected['name']}",
        icon=folium.Icon(color="red", icon="warning-sign"),
    ).add_to(map_obj)

    road_mode = route.get("routing_mode") in {"cached_osm_graph", "osrm_live", "osrm_cached"}
    if road_mode:
        folium.PolyLine(
            geometry,
            color="#ffffff",
            weight=10,
            opacity=0.75,
            name="Route casing",
        ).add_to(map_obj)
        folium.PolyLine(
            geometry,
            color="#1565c0",
            weight=6,
            opacity=0.98,
            tooltip="Recommended road route to the selected safe shelter",
            name="Recommended Safe-Shelter Route",
        ).add_to(map_obj)
    else:
        folium.PolyLine(
            geometry,
            color="#5f6368",
            weight=3,
            opacity=0.9,
            dash_array="10,10",
            tooltip="Straight-line planning fallback — road service/cache unavailable",
            name="Route Planning Fallback",
        ).add_to(map_obj)

    folium.Marker(
        [float(recommended["latitude"]), float(recommended["longitude"])],
        tooltip=f"Safe shelter: {recommended['shelter_name']}",
        popup=folium.Popup(
            f"<b>{recommended['shelter_name']}</b><br>Safety: {recommended['safety_score']:.0f}/100"
            f"<br>Available capacity: {int(recommended['available_capacity']):,}"
            f"<br>Suitability: {recommended['suitability_score']:.1f}/100",
            max_width=280,
        ),
        icon=folium.Icon(color="green", icon="home"),
    ).add_to(map_obj)

    # Keep both endpoints visible so the operator can actually inspect the path.
    map_obj.fit_bounds([list(origin), list(destination)], padding=(70, 70))

folium.LayerControl(collapsed=True).add_to(map_obj)

left, right = st.columns([2.15, 1], gap="large")
with left:
    st_folium(map_obj, height=680, width=1100, returned_objects=[])
    if selected_bhuvan is not None:
        st.success(
            f"Bhuvan context active: {selected_bhuvan['label']} · layer `{selected_bhuvan['layer']}`. "
            "This is source GIS context, not a calibrated risk input."
        )
    st.caption(
        "HIGH/CRITICAL circles are habitation-centered DEMO decision-visualization areas, not statutory hazard boundaries. "
        "The analytical GIS geometry remains unchanged. Shelter routing prefers a local OSM cache, then a live/cached OSRM road route, "
        "and only then uses an explicitly dashed straight-line fallback."
    )

with right:
    st.markdown("### Selected red-zone profile")
    st.subheader(selected["name"])
    render_risk_badge(selected["risk_level"])
    st.metric("Hazard Score", f"{selected['hazard_score']:.1f}/100")
    st.metric("Hazard Data Completeness", f"{float(selected.get('hazard_data_completeness', 0)):.0f}%")
    st.write(f"**Primary drivers:** {selected['risk_drivers']}")
    st.write(f"**Coordination zone:** {selected.get('coordination_zone','—')} (experimental grouping only)")
    st.code(f"{selected['latitude']:.5f}, {selected['longitude']:.5f}")

    st.markdown("### Recommended safe evacuation route")
    if recommended and route:
        st.success(f"{selected['name']} → {recommended['shelter_name']}")
        r1, r2 = st.columns(2)
        r1.metric("Shelter Suitability", f"{recommended['suitability_score']:.1f}/100")
        r2.metric("Available Capacity", f"{int(recommended['available_capacity']):,}")
        st.write(f"Safety: **{recommended['safety_score']:.0f}/100** · Accessibility: **{recommended['accessibility_score']:.0f}/100**")
        st.write(f"Route distance: **{route['distance_km']:.2f} km**")
        if route.get("travel_time_min") is not None:
            st.write(f"Estimated travel time: **{route['travel_time_min']:.1f} min**")

        routing_mode = route.get("routing_mode")
        if routing_mode == "cached_osm_graph":
            st.success("Road path: local cached OpenStreetMap network.")
        elif routing_mode == "osrm_live":
            st.success("Road path: live OSRM routing service.")
        elif routing_mode == "osrm_cached":
            st.info("Road path: cached result from a previous OSRM query.")
        else:
            st.warning("Road routing is unavailable; the map is showing the dashed straight-line planning fallback.")
        if route.get("route_note"):
            st.caption(route["route_note"])
    else:
        st.warning("No shelter currently passes the safety and available-capacity gates for the selected habitation.")

    if selected_bhuvan is not None:
        st.markdown("### Bhuvan provenance")
        st.write(f"**Layer:** `{selected_bhuvan['layer']}`")
        st.write(f"**Reference:** {selected_bhuvan['reference']}")
        st.caption("Historical/contextual source layer. No direct contribution to the deterministic risk score.")

st.markdown("**Risk legend:** CRITICAL = red · HIGH = orange · MODERATE = amber · LOW = green")
render_disclaimer()
