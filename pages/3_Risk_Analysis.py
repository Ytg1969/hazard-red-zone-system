import pandas as pd
import plotly.express as px
import streamlit as st

from src.hazard_model import compute_hazard_components
from src.pipeline import enrich_habitations, load_demo_data, load_demo_hazards
from src.risk_engine import DEFAULT_WEIGHTS, calculate_risk
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(page_title="Risk Analysis", layout="wide")
inject_global_css()
render_page_header("Risk Analysis", "Explainable habitation-level risk plus transparent Flood, Cyclone, Landslide, Earthquake and Drought prototype hazard profiles.")
render_data_mode_indicator("DEMO")
city, hazard_profile = render_demo_scope_controls("risk")

try:
    habitations_raw, _ = load_demo_data(city)
    hazards = load_demo_hazards()
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type=hazard_profile)
except Exception as exc:
    st.error(f"Unable to calculate risk: {exc}")
    render_disclaimer()
    st.stop()

selected_name = st.selectbox("Select habitation", habitations.sort_values("risk_score", ascending=False)["name"].tolist())
habitation = habitations[habitations["name"] == selected_name].iloc[0].to_dict()
risk = calculate_risk(habitation)

left, right = st.columns([1.2, 1.8], gap="large")
with left:
    st.subheader(habitation["name"])
    render_risk_badge(risk["risk_level"])
    st.metric("Risk Score", f"{risk['risk_score']:.1f}/100")
    st.metric("Hazard Score", f"{risk['components']['hazard']:.1f}/100")
    st.metric("Population", f"{int(habitation['population']):,}")
    st.metric("Vulnerable Population", f"{int(habitation['children_population'] + habitation['elderly_population']):,}")
    st.metric("Relocation Priority", habitation["relocation_priority"])
    st.metric("Hazard Data Completeness", f"{float(habitation.get('hazard_data_completeness',0)):.0f}%")
    st.caption(f"Coordination grouping: {habitation.get('coordination_zone','—')} · not used in the risk score")

with right:
    component_labels = {"hazard": "Hazard Intensity", "exposure": "Population Exposure", "vulnerability": "Vulnerability", "accessibility": "Evacuation Difficulty"}
    rows = [{"Factor": component_labels[key], "Raw Score": raw, "Weight": DEFAULT_WEIGHTS[key], "Contribution": risk["contributions"][key]} for key, raw in risk["components"].items()]
    contribution_df = pd.DataFrame(rows).sort_values("Contribution", ascending=True)
    fig = px.bar(contribution_df, x="Contribution", y="Factor", orientation="h", text="Contribution", title="Weighted Contribution to Final Risk Score")
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(height=360, margin=dict(l=20, r=45, t=55, b=20))
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Transparent hazard-profile breakdown")
if hazard_profile == "stored":
    st.info("Stored / GIS hazard score selected. Choose a named hazard profile to inspect indicator math.")
else:
    try:
        source_row = habitations_raw[habitations_raw["habitation_id"].astype(str) == str(habitation["habitation_id"])]
        breakdown = compute_hazard_components(source_row, hazard_profile)
        active_weights = breakdown.attrs.get("active_weights", {})
        labels = breakdown.attrs.get("labels", {})
        if hazard_profile == "combined":
            model_rows = []
            for model in breakdown.attrs.get("active_models", []):
                model_rows.append({"Hazard": model.title(), "Score": float(breakdown[f"{model}_hazard_score"].iloc[0]), "Active Weight": float(breakdown[f"{model}_weight"].iloc[0])})
            st.plotly_chart(px.bar(pd.DataFrame(model_rows), x="Hazard", y="Score", color="Active Weight", range_y=[0,100], title="Combined Multi-Hazard Components"), width="stretch")
            st.dataframe(pd.DataFrame(model_rows), width="stretch", hide_index=True)
        else:
            detail_rows = []
            for indicator, active_weight in active_weights.items():
                detail_rows.append({"Indicator": labels.get(indicator, indicator), "Normalized Score": float(breakdown[indicator].iloc[0]), "Active Weight": active_weight, "Contribution": float(breakdown[f"{indicator}_contribution"].iloc[0])})
            detail_df = pd.DataFrame(detail_rows).sort_values("Contribution", ascending=False)
            st.dataframe(detail_df, width="stretch", hide_index=True)
            st.plotly_chart(px.bar(detail_df, x="Contribution", y="Indicator", orientation="h", title=f"{hazard_profile.title()} Hazard Contributions"), width="stretch")
        st.caption("Prototype indicator bounds and weights are explicit in src/hazard_model.py. They are demonstration assumptions, not official hazard standards.")
    except Exception as exc:
        st.info(f"Hazard indicator breakdown unavailable: {exc}")

st.divider()
summary_left, summary_right = st.columns(2, gap="large")
with summary_left:
    st.subheader("Why this location is classified this way")
    sorted_components = sorted(risk["components"].items(), key=lambda item: risk["contributions"][item[0]], reverse=True)
    for key, value in sorted_components:
        st.write(f"**{component_labels[key]}:** {value:.1f}/100 × {DEFAULT_WEIGHTS[key]:.0%} = **{risk['contributions'][key]:.1f} risk points**")
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

st.subheader("Final Risk Factor Detail")
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
render_disclaimer()
