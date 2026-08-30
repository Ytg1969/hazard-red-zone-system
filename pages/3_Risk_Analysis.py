import pandas as pd
import plotly.express as px
import streamlit as st

from src.pipeline import enrich_habitations, load_demo_data, load_demo_hazards
from src.risk_engine import DEFAULT_WEIGHTS, calculate_risk
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(page_title="Risk Analysis", layout="wide")
inject_global_css()
render_page_header(
    "Risk Analysis",
    "Explainable habitation-level risk assessment using hazard, exposure, vulnerability and evacuation difficulty.",
)
render_data_mode_indicator("DEMO")

try:
    habitations_raw, _ = load_demo_data()
    try:
        hazards = load_demo_hazards()
    except Exception:
        hazards = None
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards)
except Exception:
    st.error("Unable to calculate habitation risk from the demonstration dataset.")
    render_disclaimer()
    st.stop()

options = habitations.sort_values("risk_score", ascending=False)["name"].tolist()
selected_name = st.selectbox("Select habitation", options)
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
    if habitation.get("hazard_type"):
        st.caption(f"Nearest/intersecting hazard type: {habitation['hazard_type']}")

with right:
    component_labels = {
        "hazard": "Hazard Intensity",
        "exposure": "Population Exposure",
        "vulnerability": "Vulnerability",
        "accessibility": "Evacuation Difficulty",
    }
    rows = []
    for key, raw_score in risk["components"].items():
        rows.append(
            {
                "Factor": component_labels[key],
                "Raw Score": raw_score,
                "Weight": DEFAULT_WEIGHTS[key],
                "Contribution": raw_score * DEFAULT_WEIGHTS[key],
            }
        )
    contribution_df = pd.DataFrame(rows).sort_values("Contribution", ascending=True)
    fig = px.bar(
        contribution_df,
        x="Contribution",
        y="Factor",
        orientation="h",
        text="Contribution",
        title="Weighted Contribution to Risk Score",
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(height=360, margin=dict(l=20, r=45, t=55, b=20))
    st.plotly_chart(fig, width="stretch")

st.divider()
summary_left, summary_right = st.columns(2, gap="large")
with summary_left:
    st.subheader("Why this location is classified this way")
    sorted_components = sorted(
        risk["components"].items(), key=lambda item: item[1] * DEFAULT_WEIGHTS[item[0]], reverse=True
    )
    for key, value in sorted_components:
        contribution = value * DEFAULT_WEIGHTS[key]
        st.write(
            f"**{component_labels[key]}:** {value:.1f}/100 × {DEFAULT_WEIGHTS[key]:.0%} "
            f"= **{contribution:.1f} risk points**"
        )

with summary_right:
    st.subheader("Potential mitigation focus")
    top_driver = sorted_components[0][0]
    recommendations = {
        "hazard": "Prioritize hazard monitoring, protective works, early warning and exposure reduction in the active hazard footprint.",
        "exposure": "Reduce exposed population through phased movement, land-use controls and temporary evacuation planning.",
        "vulnerability": "Prioritize children, elderly people and other vulnerable groups in transport, shelter and medical planning.",
        "accessibility": "Improve evacuation access, route redundancy, transport staging and road-clearance planning.",
    }
    st.info(recommendations[top_driver])
    st.caption(
        "These are decision-support suggestions derived from the dominant modeled factor; they are not engineering or statutory prescriptions."
    )

st.subheader("Factor Detail")
st.dataframe(
    pd.DataFrame(rows),
    width="stretch",
    hide_index=True,
    column_config={
        "Raw Score": st.column_config.NumberColumn(format="%.1f"),
        "Weight": st.column_config.NumberColumn(format="%.0f%%"),
        "Contribution": st.column_config.NumberColumn(format="%.1f"),
    },
)

render_disclaimer()
