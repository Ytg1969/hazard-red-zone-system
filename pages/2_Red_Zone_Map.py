import folium
import streamlit as st
from streamlit_folium import st_folium

from src.pipeline import enrich_habitations, load_demo_data
from src.ui_theme import (
    RISK_COLORS,
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(page_title="Red Zone Map", layout="wide")
inject_global_css()
render_page_header(
    "Red Zone Map",
    "Spatial view of habitation risk classes. Demonstration points are shown until authoritative hazard layers are integrated.",
)
render_data_mode_indicator("DEMO")

try:
    habitations_raw, _ = load_demo_data()
    habitations = enrich_habitations(habitations_raw)
except Exception:
    st.error("Unable to load the demonstration habitation layer.")
    render_disclaimer()
    st.stop()

with st.sidebar:
    st.subheader("Map Filters")
    risk_levels = st.multiselect(
        "Risk levels",
        ["CRITICAL", "HIGH", "MODERATE", "LOW"],
        default=["CRITICAL", "HIGH", "MODERATE", "LOW"],
    )
    district_options = ["All"] + sorted(habitations["district_code"].dropna().astype(str).unique().tolist())
    district = st.selectbox("District", district_options)
    show_population = st.checkbox("Scale markers by population", value=True)

filtered = habitations[habitations["risk_level"].isin(risk_levels)].copy()
if district != "All":
    filtered = filtered[filtered["district_code"].astype(str) == district]

if filtered.empty:
    st.info("No habitations match the selected map filters.")
    render_disclaimer()
    st.stop()

selected_name = st.selectbox(
    "Inspect habitation",
    filtered.sort_values("risk_score", ascending=False)["name"].tolist(),
)
selected = filtered[filtered["name"] == selected_name].iloc[0]

map_center = [float(filtered["latitude"].mean()), float(filtered["longitude"].mean())]
map_obj = folium.Map(location=map_center, zoom_start=10, tiles="OpenStreetMap", control_scale=True)

for row in filtered.to_dict(orient="records"):
    radius = 8
    if show_population:
        radius = max(6, min(18, 5 + float(row["population"]) / 300))
    color = RISK_COLORS.get(row["risk_level"], "#6c757d")
    popup = (
        f"<b>{row['name']}</b><br>"
        f"Risk: {row['risk_score']:.1f} / {row['risk_level']}<br>"
        f"Population: {int(row['population']):,}<br>"
        f"Priority: {row['relocation_priority']}"
    )
    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=radius,
        popup=folium.Popup(popup, max_width=260),
        tooltip=f"{row['name']} — {row['risk_level']}",
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.78,
        weight=2,
    ).add_to(map_obj)

left, right = st.columns([2.2, 1], gap="large")
with left:
    st_folium(map_obj, height=620, width=1000, returned_objects=[])
    st.caption(
        "Current map uses habitation points and computed risk classes. Real hazard polygons/rasters are a GIS integration task, not simulated here."
    )

with right:
    st.subheader(selected["name"])
    render_risk_badge(selected["risk_level"])
    st.metric("Risk Score", f"{selected['risk_score']:.1f}/100")
    st.metric("Population", f"{int(selected['population']):,}")
    st.metric("Relocation Priority", selected["relocation_priority"])
    st.markdown("**Primary drivers**")
    st.write(selected["risk_drivers"])
    st.markdown("**Coordinates**")
    st.code(f"{selected['latitude']:.5f}, {selected['longitude']:.5f}")

st.markdown(
    "**Legend:** "
    "CRITICAL = red · HIGH = orange · MODERATE = amber · LOW = green"
)
render_disclaimer()
