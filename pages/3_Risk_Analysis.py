import pandas as pd
import plotly.express as px
import streamlit as st

from src.hazard_model import compute_hazard_components
from src.operational_hazards import geojson_to_gdf
from src.pipeline import enrich_habitations, load_demo_data, load_demo_hazards
from src.risk_engine import DEFAULT_WEIGHTS, calculate_risk
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_demo_scope_controls, render_disclaimer, render_page_header, render_risk_badge

st.set_page_config(page_title="Risk Analysis", layout="wide")
inject_global_css()
render_page_header("Risk Analysis", "Explainable habitation-level H/E/V/A risk with operational or fallback demonstration inputs.")

workspace = st.session_state.get("operational_workspace")
operational = bool(workspace)
if operational:
    mode = workspace.get("habitation_mode", "UNVERIFIED")
    render_data_mode_indicator(mode if mode in {"LIVE", "CACHED", "DEMO"} else "DEMO")
    area_label = workspace.get("label", "Operational area")
    habitations_raw = pd.DataFrame(workspace["habitations"])
    hazard_profile = st.sidebar.selectbox("Analytical hazard profile", ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"], index=0, format_func=lambda v: "Stored / calibrated GIS" if v == "stored" else v.title())
    hazard_data = None
    if hazard_profile == "stored" and st.session_state.get("operational_hazard_geojson"):
        hazard_data = geojson_to_gdf(st.session_state["operational_hazard_geojson"])
    st.sidebar.success(f"Operational workspace: {area_label}")
    st.sidebar.page_link("pages/9_Operational_Data.py", label="Manage operational data")
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("risk")
    area_label = city
    habitations_raw, _ = load_demo_data(city)
    hazard_data = load_demo_hazards()

try:
    habitations = enrich_habitations(habitations_raw, hazard_data=hazard_data, hazard_type=hazard_profile, add_coordination_zones=not operational)
except Exception as exc:
    st.error(f"Unable to calculate risk: {exc}")
    render_disclaimer()
    st.stop()

st.caption(f"Active scope: **{area_label}** · Risk = 0.35H + 0.25E + 0.25V + 0.15A")
selected_name = st.selectbox("Select habitation", habitations.sort_values("risk_score", ascending=False)["name"].tolist())
habitation = habitations[habitations["name"] == selected_name].iloc[0].to_dict()
risk = calculate_risk(habitation)

left, right = st.columns([1.15, 1.85], gap="large")
with left:
    st.subheader(habitation["name"])
    render_risk_badge(risk["risk_level"])
    st.metric("Risk Score", f"{risk['risk_score']:.1f}/100")
    st.metric("Hazard Score", f"{risk['components']['hazard']:.1f}/100")
    st.metric("Population", f"{int(habitation['population']):,}")
    st.metric("Vulnerable Population", f"{int(habitation['children_population'] + habitation['elderly_population']):,}")
    st.metric("Relocation Priority", habitation["relocation_priority"])
    if habitation.get("inside_hazard_zone") is not None:
        st.caption(f"GIS intersection: {habitation.get('inside_hazard_zone')} · nearest hazard distance: {habitation.get('distance_to_hazard_km')} km")
with right:
    labels = {"hazard": "Hazard Intensity", "exposure": "Population Exposure", "vulnerability": "Vulnerability", "accessibility": "Evacuation Difficulty"}
    rows = [{"Factor": labels[k], "Raw Score": raw, "Weight": DEFAULT_WEIGHTS[k], "Contribution": risk["contributions"][k]} for k, raw in risk["components"].items()]
    contribution_df = pd.DataFrame(rows).sort_values("Contribution", ascending=True)
    fig = px.bar(contribution_df, x="Contribution", y="Factor", orientation="h", text="Contribution", title="Weighted contribution to final risk")
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(height=360, margin=dict(l=20, r=45, t=55, b=20))
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Hazard evidence")
if hazard_profile == "stored":
    if operational and hazard_data is not None:
        st.success(f"Using calibrated uploaded GIS layer: {st.session_state.get('operational_hazard_name', 'GeoJSON')}")
        detail = {k: habitation.get(k) for k in ["gis_hazard_score", "gis_hazard_source", "gis_hazard_type", "inside_hazard_zone", "distance_to_hazard_km"] if k in habitation}
        st.json(detail)
    else:
        st.info("Using the stored hazard_score supplied with the habitation dataset. No external live observation silently changes this score.")
else:
    try:
        source_row = habitations_raw[habitations_raw["habitation_id"].astype(str) == str(habitation["habitation_id"])]
        breakdown = compute_hazard_components(source_row, hazard_profile)
        if hazard_profile == "combined":
            model_rows = [{"Hazard": model.title(), "Score": float(breakdown[f"{model}_hazard_score"].iloc[0]), "Active Weight": float(breakdown[f"{model}_weight"].iloc[0])} for model in breakdown.attrs.get("active_models", [])]
            st.plotly_chart(px.bar(pd.DataFrame(model_rows), x="Hazard", y="Score", color="Active Weight", range_y=[0, 100], title="Combined multi-hazard components"), width="stretch")
            st.dataframe(pd.DataFrame(model_rows), width="stretch", hide_index=True)
        else:
            active_weights = breakdown.attrs.get("active_weights", {})
            labels2 = breakdown.attrs.get("labels", {})
            detail_rows = [{"Indicator": labels2.get(indicator, indicator), "Normalized Score": float(breakdown[indicator].iloc[0]), "Active Weight": weight, "Contribution": float(breakdown[f"{indicator}_contribution"].iloc[0])} for indicator, weight in active_weights.items()]
            detail_df = pd.DataFrame(detail_rows).sort_values("Contribution", ascending=False)
            st.dataframe(detail_df, width="stretch", hide_index=True)
            st.plotly_chart(px.bar(detail_df, x="Contribution", y="Indicator", orientation="h", title=f"{hazard_profile.title()} hazard contributions"), width="stretch")
        st.caption("Prototype indicator mappings remain transparent assumptions until replaced by a verified source-specific calibration.")
    except Exception as exc:
        st.info(f"Hazard indicator breakdown unavailable: {exc}")

st.divider()
summary_left, summary_right = st.columns(2, gap="large")
with summary_left:
    st.subheader("Why this location is classified this way")
    sorted_components = sorted(risk["components"].items(), key=lambda item: risk["contributions"][item[0]], reverse=True)
    for key, value in sorted_components:
        st.write(f"**{labels[key]}:** {value:.1f}/100 × {DEFAULT_WEIGHTS[key]:.0%} = **{risk['contributions'][key]:.1f} points**")
with summary_right:
    st.subheader("Potential mitigation focus")
    top_driver = sorted_components[0][0]
    recommendations = {
        "hazard": "Prioritize hazard monitoring, protective works, early warning and exposure reduction.",
        "exposure": "Reduce exposed population through phased movement and land-use controls.",
        "vulnerability": "Prioritize children, elderly people and other vulnerable groups in transport, shelter and medical planning.",
        "accessibility": "Improve route redundancy, transport staging and road-clearance planning.",
    }
    st.info(recommendations[top_driver])

st.subheader("Final risk-factor detail")
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
render_disclaimer()
