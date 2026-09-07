import os
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium

from src.bhuvan_layers import layers_for_city
from src.operational_hazards import geojson_to_gdf
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.relocation import rank_shelters
from src.routing import estimate_route
from src.runtime_mode import offline_mode
from src.streamlit_workspace import resolve_operational_hazard, resolve_operational_workspace
from src.ui_theme import (
    RISK_COLORS,
    inject_global_css,
    render_context_bar,
    render_data_mode_indicator,
    render_decision_gate,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
    render_section_header,
    render_source_card,
)

ROAD_GRAPH_FILES = {
    "Puri": Path("data/cache/roads/Puri_Odisha_India.graphml"),
    "Guwahati": Path("data/cache/roads/Guwahati_Assam_India.graphml"),
    "Chennai": Path("data/cache/roads/Chennai_Tamil_Nadu_India.graphml"),
}


def _red_zone_radius_m(risk_score: float) -> float:
    score = max(50.0, min(100.0, float(risk_score)))
    return 650.0 + (score - 50.0) * 24.0


st.set_page_config(page_title="Hazard Map", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
render_page_header(
    "Hazard Map",
    "A map-first operational canvas for red zones, exposed people, qualified shelters and route provenance.",
)

is_offline = offline_mode()
resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds are unavailable: {exc}")

operational = bool(resolved)
selected_bhuvan = None
hazard_source = None

if operational:
    workspace = resolved["payload"]
    mode = str(workspace.get("habitation_mode", "UNVERIFIED")).upper()
    area_label = str(workspace.get("label", "Operational area"))
    with st.sidebar:
        st.markdown("### Map context")
        hazard_profile = st.selectbox(
            "Hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda v: "Stored / calibrated GIS" if v == "stored" else v.title(),
        )
        st.success(f"Scope: {area_label}")
    habitations_raw = resolved["habitations"]
    shelters_raw = resolved["shelters"]
    hazard_data = None
    if hazard_profile == "stored":
        try:
            hazard_source = resolve_operational_hazard(auto_configured=True)
            if hazard_source:
                hazard_data = geojson_to_gdf(hazard_source["geojson"])
        except Exception as exc:
            st.error(f"Configured operational hazard layer could not be loaded: {exc}")
            st.stop()
else:
    mode = "DEMO"
    city, hazard_profile = render_demo_scope_controls("map")
    area_label = city
    habitations_raw, shelters_raw = load_demo_data(city)
    hazard_data = load_demo_hazards()

try:
    habitations = enrich_habitations(
        habitations_raw,
        hazard_data=hazard_data,
        hazard_type=hazard_profile,
        add_coordination_zones=not operational,
    )
    shelters = enrich_shelters(shelters_raw)
except Exception as exc:
    st.error(f"Unable to prepare hazard map: {exc}")
    render_disclaimer()
    st.stop()

with st.sidebar:
    st.markdown("### Display")
    risk_levels = st.multiselect(
        "Visible risk levels",
        ["CRITICAL", "HIGH", "MODERATE", "LOW"],
        default=["CRITICAL", "HIGH", "MODERATE", "LOW"],
    )
    with st.expander("Layers & routing", expanded=False):
        show_red_zones = st.checkbox("Decision zones", value=True)
        show_shelters = st.checkbox("Qualified shelters", value=True)
        show_route = st.checkbox("Selected route", value=True)
        show_population = st.checkbox("Population-scaled markers", value=True)
        allow_live_route = st.checkbox(
            "Live road routing if cache is missing",
            value=not is_offline,
            disabled=is_offline,
        )
        if not operational and not is_offline:
            bhuvan_options = layers_for_city(city)
            if bhuvan_options and st.checkbox("Authoritative Bhuvan context", value=False):
                labels = [item["label"] for item in bhuvan_options]
                chosen = st.selectbox("Bhuvan layer", labels)
                selected_bhuvan = next(item for item in bhuvan_options if item["label"] == chosen)
                st.caption("Context only; overlay does not alter analytical risk.")

filtered = habitations[habitations["risk_level"].isin(risk_levels)].copy()
if filtered.empty:
    st.info("No locations match the current risk filter.")
    st.stop()

priority_names = filtered.sort_values("risk_score", ascending=False)["name"].astype(str).tolist()
remembered = st.session_state.get("focus_location")
default_index = priority_names.index(remembered) if remembered in priority_names else 0
with st.sidebar:
    st.markdown("### Focus & route")
    selected_name = st.selectbox("Inspect location", priority_names, index=default_index, key="map_focus")
st.session_state["focus_location"] = selected_name
selected = filtered[filtered["name"].astype(str) == str(selected_name)].iloc[0]

local_shelters = shelters
if not operational and selected.get("demo_city") and "demo_city" in shelters.columns:
    local_shelters = shelters[shelters["demo_city"] == selected["demo_city"]].copy()
ranked_shelters = rank_shelters(selected.to_dict(), local_shelters)

selected_shelter_name = None
if ranked_shelters:
    shelter_labels = [
        f"#{index + 1} {item['shelter_name']} · {item['suitability_score']:.0f}/100 · {int(item['available_capacity']):,} spaces"
        for index, item in enumerate(ranked_shelters[:8])
    ]
    with st.sidebar:
        chosen_shelter = st.selectbox("Qualified shelter", shelter_labels)
    selected_shelter_name = ranked_shelters[shelter_labels.index(chosen_shelter)]["shelter_name"]

render_context_bar(
    str(area_label),
    f"{hazard_profile.replace('_', ' ').title()} · {mode}",
    "MAP / SHELTER / ROUTE",
)
if mode in {"LIVE", "CACHED", "DEMO"}:
    render_data_mode_indicator(mode)
else:
    st.warning("Operational workspace provenance is UNVERIFIED.")

render_kpi_strip([
    ("Risk", f"{selected['risk_score']:.1f}/100", str(selected["risk_level"])),
    ("Population", f"{int(selected['population']):,}", "Selected location"),
    ("Priority", selected["relocation_priority"], "Decision-support priority"),
    ("Safe candidates", len(ranked_shelters), "Passed safety + capacity gates"),
    ("Evidence", f"{float(selected.get('hazard_data_completeness', 0) or 0):.0f}%", "Hazard evidence completeness"),
])

if is_offline:
    st.info("Offline field mode: remote basemap/GIS calls are disabled; local vectors and cached/fallback routing remain available.")

map_center = [float(filtered["latitude"].mean()), float(filtered["longitude"].mean())]
map_obj = folium.Map(location=map_center, zoom_start=10 if len(filtered) < 80 else 8, tiles=None, control_scale=True)
if not is_offline:
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors",
        name="OpenStreetMap",
        overlay=False,
        control=False,
        max_zoom=19,
    ).add_to(map_obj)

if selected_bhuvan:
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

if show_red_zones:
    for row in filtered[filtered["risk_level"].isin(["HIGH", "CRITICAL"])].to_dict(orient="records"):
        color = RISK_COLORS.get(row["risk_level"], "#dc3545")
        selected_row = str(row["name"]) == str(selected_name)
        folium.Circle(
            [float(row["latitude"]), float(row["longitude"])],
            radius=_red_zone_radius_m(row["risk_score"]),
            color=color,
            weight=3 if selected_row else 2,
            fill=True,
            fill_color=color,
            fill_opacity=.18 if selected_row else .07,
            tooltip=f"{row['name']} · {row['risk_level']} · {row['risk_score']:.1f}/100",
        ).add_to(map_obj)

for row in filtered.to_dict(orient="records"):
    selected_row = str(row["name"]) == str(selected_name)
    radius = max(6, min(18, 5 + float(row["population"]) / 350)) if show_population else 8
    color = RISK_COLORS.get(row["risk_level"], "#6c757d")
    folium.CircleMarker(
        [row["latitude"], row["longitude"]],
        radius=radius,
        popup=folium.Popup(
            f"<b>{row['name']}</b><br>Risk {row['risk_score']:.1f}/100 · {row['risk_level']}<br>Population {int(row['population']):,}<br>Priority {row['relocation_priority']}",
            max_width=320,
        ),
        tooltip=f"{row['name']} — {row['risk_level']}",
        color="#07101A" if selected_row else "#ffffff",
        fill=True,
        fill_color=color,
        fill_opacity=.98,
        weight=4 if selected_row else 2,
    ).add_to(map_obj)

if show_shelters:
    for index, shelter in enumerate(ranked_shelters):
        target = shelter["shelter_name"] == selected_shelter_name
        folium.Marker(
            [float(shelter["latitude"]), float(shelter["longitude"])],
            tooltip=f"Qualified shelter #{index + 1}: {shelter['shelter_name']}",
            popup=folium.Popup(
                f"<b>{shelter['shelter_name']}</b><br>Safety {shelter['safety_score']:.0f}/100<br>Available {int(shelter['available_capacity']):,}<br>Suitability {shelter['suitability_score']:.1f}/100",
                max_width=320,
            ),
            icon=folium.Icon(color="green" if target else "lightgreen", icon="home"),
        ).add_to(map_obj)

route = None
recommended = next(
    (item for item in ranked_shelters if item["shelter_name"] == selected_shelter_name),
    ranked_shelters[0] if ranked_shelters else None,
)
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
        folium.PolyLine(geometry, color="#ffffff", weight=8, opacity=.48).add_to(map_obj)
        folium.PolyLine(geometry, color="#5BA9FF", weight=4, opacity=.98, tooltip="Qualified-shelter route").add_to(map_obj)
    else:
        folium.PolyLine(geometry, color="#9AA7B5", weight=3, dash_array="9,9", tooltip="Straight-line fallback").add_to(map_obj)
    map_obj.fit_bounds([list(origin), list(destination)], padding=(70, 70))

folium.LayerControl(collapsed=True).add_to(map_obj)

render_section_header(
    "Operational canvas",
    "Map interaction remains primary; decision detail is kept in the contextual panel.",
    str(selected_name),
)
map_col, detail_col = st.columns([3.15, 1], gap="large")
with map_col:
    st_folium(map_obj, height=735, width=1400, returned_objects=[])
    st.caption("HIGH/CRITICAL circles are decision-support visualization areas, not statutory hazard boundaries.")
with detail_col:
    st.markdown(f"### {selected['name']}")
    render_risk_badge(selected["risk_level"])
    st.caption(f"{int(selected['population']):,} people · {selected['relocation_priority']} priority")
    st.write(f"**Drivers** · {selected['risk_drivers']}")

    if ranked_shelters:
        st.markdown("#### Qualified destination")
        render_source_card(
            recommended["shelter_name"],
            f"{recommended['suitability_score']:.1f}/100 suitability",
            f"{int(recommended['available_capacity']):,} available · safety {recommended['safety_score']:.0f}/100",
        )
        if route:
            route_mode = str(route.get("routing_mode", "unknown"))
            road_route = route_mode in {"cached_osm_graph", "osrm_live", "osrm_cached"}
            render_decision_gate(
                "Route evidence",
                f"{route['distance_km']:.2f} km · {route_mode}",
                "ok" if road_route else "warn",
            )
            if route.get("travel_time_min") is not None:
                st.caption(f"Travel estimate {route['travel_time_min']:.1f} min")
            if route.get("route_note"):
                st.caption(str(route["route_note"]))
        st.page_link("pages/4_Relocation_Planner.py", label="⇢  Build relocation plan", use_container_width=True)
    else:
        st.error("No shelter passes both safety and available-capacity gates for this location.")

    st.markdown("#### Evidence status")
    if operational and hazard_data is not None:
        st.success(f"Calibrated hazard source: {hazard_source.get('label', 'GeoJSON') if hazard_source else 'GeoJSON'}")
    elif operational and hazard_profile == "stored":
        st.info("Stored operational hazard score active; no calibrated GeoJSON is active.")
    else:
        st.caption("Demo/synthetic hazard context is separated from authoritative operational evidence.")
    st.page_link("pages/3_Risk_Analysis.py", label="◒  Explain this risk", use_container_width=True)

render_disclaimer()
