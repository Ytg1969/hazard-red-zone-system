import pandas as pd
import plotly.express as px
import streamlit as st

from src.hazard_model import compute_hazard_components
from src.operational_hazards import geojson_to_gdf
from src.pipeline import enrich_habitations, load_demo_data, load_demo_hazards
from src.risk_engine import DEFAULT_WEIGHTS, calculate_risk
from src.streamlit_workspace import resolve_operational_hazard, resolve_operational_workspace
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
    render_source_card,
)

st.set_page_config(page_title="Risk Intelligence", layout="wide", initial_sidebar_state="auto")
inject_global_css()
render_page_header(
    "Risk Intelligence",
    "Understand exactly why a location is risky, which factor contributes most, and what evidence supports the score.",
)

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds are unavailable: {exc}")

operational = bool(resolved)
hazard_source = None
if operational:
    workspace = resolved["payload"]
    mode = workspace.get("habitation_mode", "UNVERIFIED")
    if mode in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(mode)
    else:
        st.warning("Operational workspace provenance is UNVERIFIED.")
    area_label = workspace.get("label", "Operational area")
    habitations_raw = resolved["habitations"]
    hazard_profile = st.sidebar.selectbox(
        "Analytical hazard profile",
        ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
        index=0,
        format_func=lambda v: "Stored / calibrated GIS" if v == "stored" else v.title(),
    )
    hazard_data = None
    if hazard_profile == "stored":
        try:
            hazard_source = resolve_operational_hazard(auto_configured=True)
            if hazard_source:
                hazard_data = geojson_to_gdf(hazard_source["geojson"])
        except Exception as exc:
            st.error(f"Configured operational hazard layer could not be loaded: {exc}")
            st.stop()
    st.sidebar.success(f"Operational workspace: {area_label}")
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("risk")
    area_label = city
    habitations_raw, _ = load_demo_data(city)
    hazard_data = load_demo_hazards()

try:
    habitations = enrich_habitations(
        habitations_raw,
        hazard_data=hazard_data,
        hazard_type=hazard_profile,
        add_coordination_zones=not operational,
    )
except Exception as exc:
    st.error(f"Unable to calculate risk: {exc}")
    render_disclaimer()
    st.stop()

ordered = habitations.sort_values("risk_score", ascending=False)
selected_name = st.selectbox("Inspect location", ordered["name"].tolist())
habitation = habitations[habitations["name"] == selected_name].iloc[0].to_dict()
risk = calculate_risk(habitation)

labels = {
    "hazard": "Hazard",
    "exposure": "Exposure",
    "vulnerability": "Vulnerability",
    "accessibility": "Evacuation difficulty",
}
rows = [
    {
        "Factor": labels[key],
        "Raw Score": float(raw),
        "Weight": float(DEFAULT_WEIGHTS[key]),
        "Contribution": float(risk["contributions"][key]),
    }
    for key, raw in risk["components"].items()
]
contribution_df = pd.DataFrame(rows).sort_values("Contribution", ascending=False)
top_driver_key = max(risk["components"], key=lambda key: risk["contributions"][key])
top_driver = labels[top_driver_key]

st.caption(f"{area_label} · {hazard_profile.replace('_', ' ').title()} · Risk = 0.35H + 0.25E + 0.25V + 0.15A")
render_kpi_strip([
    ("Risk", f"{risk['risk_score']:.1f}/100", risk["risk_level"]),
    ("Top driver", top_driver, f"{risk['contributions'][top_driver_key]:.1f} risk points"),
    ("Population", f"{int(habitation['population']):,}", "People exposed"),
    ("Vulnerable", f"{int(habitation['children_population'] + habitation['elderly_population']):,}", "Children + elderly"),
    ("Priority", habitation["relocation_priority"], "Decision-support priority"),
])

st.markdown("## Why this location is at risk")
left, right = st.columns([1.55, 1], gap="large")
with left:
    st.markdown(f"### {habitation['name']}")
    render_risk_badge(risk["risk_level"])
    fig = px.bar(
        contribution_df.sort_values("Contribution"),
        x="Contribution",
        y="Factor",
        orientation="h",
        text="Contribution",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(height=300, margin=dict(l=10, r=35, t=10, b=10), xaxis_title="Risk points", yaxis_title="")
    st.plotly_chart(fig, width="stretch")
with right:
    recommendations = {
        "hazard": "Prioritize hazard monitoring, protective works, early warning and exposure reduction.",
        "exposure": "Reduce exposed population through phased movement and land-use controls.",
        "vulnerability": "Prioritize children, elderly people and other vulnerable groups in transport, shelter and medical planning.",
        "accessibility": "Improve route redundancy, transport staging and road-clearance planning.",
    }
    render_source_card(
        "Dominant driver",
        top_driver,
        recommendations[top_driver_key],
    )
    if habitation.get("inside_hazard_zone") is not None:
        render_source_card(
            "GIS relationship",
            "Inside" if habitation.get("inside_hazard_zone") else "Outside",
            f"Nearest hazard distance: {habitation.get('distance_to_hazard_km')} km",
        )
    completeness = float(habitation.get("hazard_data_completeness", 0) or 0)
    st.progress(max(0.0, min(1.0, completeness / 100.0)), text=f"Hazard evidence completeness {completeness:.0f}%")

st.markdown("## Component explanation")
component_cols = st.columns(4, gap="small")
for column, row in zip(component_cols, rows):
    with column:
        render_source_card(
            row["Factor"],
            f"{row['Raw Score']:.1f}/100",
            f"Weight {row['Weight']:.0%} → {row['Contribution']:.1f} risk points",
        )

st.markdown("## Compare with the active scope")
compare_cols = [c for c in ["name", "population", "risk_score", "risk_level", "relocation_priority"] if c in ordered.columns]
comparison = ordered[compare_cols].head(10).copy()
st.dataframe(
    comparison,
    width="stretch",
    hide_index=True,
    column_config={
        "risk_score": st.column_config.ProgressColumn("Risk", min_value=0, max_value=100, format="%.1f"),
        "population": st.column_config.NumberColumn("Population", format=",%d"),
    },
)

with st.expander("Hazard evidence & calibration", expanded=False):
    if hazard_profile == "stored":
        if operational and hazard_data is not None:
            source_label = hazard_source.get("label", "Calibrated hazard GeoJSON") if hazard_source else "Calibrated hazard GeoJSON"
            source_mode = hazard_source.get("mode", "SESSION") if hazard_source else "SESSION"
            st.success(f"Using calibrated GIS layer: {source_label} · {source_mode}")
            detail = {
                key: habitation.get(key)
                for key in ["gis_hazard_score", "gis_hazard_source", "gis_hazard_type", "inside_hazard_zone", "distance_to_hazard_km"]
                if key in habitation
            }
            st.json(detail)
        else:
            st.info("Using the stored hazard_score supplied with the habitation dataset. No external live observation silently changes this score.")
    else:
        try:
            source_row = habitations_raw[habitations_raw["habitation_id"].astype(str) == str(habitation["habitation_id"])]
            breakdown = compute_hazard_components(source_row, hazard_profile)
            if hazard_profile == "combined":
                model_rows = [
                    {
                        "Hazard": model.title(),
                        "Score": float(breakdown[f"{model}_hazard_score"].iloc[0]),
                        "Active Weight": float(breakdown[f"{model}_weight"].iloc[0]),
                    }
                    for model in breakdown.attrs.get("active_models", [])
                ]
                st.dataframe(pd.DataFrame(model_rows), width="stretch", hide_index=True)
            else:
                active_weights = breakdown.attrs.get("active_weights", {})
                labels2 = breakdown.attrs.get("labels", {})
                detail_rows = [
                    {
                        "Indicator": labels2.get(indicator, indicator),
                        "Normalized Score": float(breakdown[indicator].iloc[0]),
                        "Active Weight": weight,
                        "Contribution": float(breakdown[f"{indicator}_contribution"].iloc[0]),
                    }
                    for indicator, weight in active_weights.items()
                ]
                st.dataframe(pd.DataFrame(detail_rows).sort_values("Contribution", ascending=False), width="stretch", hide_index=True)
            st.caption("Prototype indicator mappings remain transparent assumptions until replaced by a verified source-specific calibration.")
        except Exception as exc:
            st.info(f"Hazard indicator breakdown unavailable: {exc}")

with st.expander("Exact risk calculation", expanded=False):
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.code("Risk = 0.35H + 0.25E + 0.25V + 0.15A")

st.markdown("## Continue decision flow")
next_left, next_right = st.columns(2, gap="large")
with next_left:
    st.page_link("pages/2_Red_Zone_Map.py", label="← Return to hazard map", use_container_width=True)
with next_right:
    st.page_link("pages/4_Relocation_Planner.py", label="Build relocation plan →", use_container_width=True)

render_disclaimer()
