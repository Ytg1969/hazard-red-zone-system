import pandas as pd
import plotly.express as px
import streamlit as st

from src.pipeline import enrich_habitations, load_demo_data
from src.risk_engine import DEFAULT_WEIGHTS
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_page_header,
)

st.set_page_config(page_title="Scenario Studio", layout="wide")
inject_global_css()
render_page_header(
    "Scenario Studio",
    "Adjust risk-factor emphasis and measure how classifications change. Scenario outputs are decision-support comparisons, not official thresholds.",
)
render_data_mode_indicator("DEMO")

try:
    habitations_raw, _ = load_demo_data()
except Exception:
    st.error("Unable to load the demonstration habitation dataset.")
    render_disclaimer()
    st.stop()

PRESETS = {
    "Recommended / Balanced": DEFAULT_WEIGHTS,
    "Hazard Priority": {"hazard": 0.50, "exposure": 0.20, "vulnerability": 0.15, "accessibility": 0.15},
    "Vulnerability Priority": {"hazard": 0.25, "exposure": 0.20, "vulnerability": 0.40, "accessibility": 0.15},
    "Evacuation Access Priority": {"hazard": 0.25, "exposure": 0.20, "vulnerability": 0.20, "accessibility": 0.35},
}

preset_name = st.selectbox("Scenario preset", list(PRESETS))
preset = PRESETS[preset_name]

st.markdown("### Risk factor emphasis")
cols = st.columns(4)
raw_values = {}
labels = {
    "hazard": "Hazard",
    "exposure": "Exposure",
    "vulnerability": "Vulnerability",
    "accessibility": "Evacuation Difficulty",
}
for col, key in zip(cols, ["hazard", "exposure", "vulnerability", "accessibility"]):
    with col:
        raw_values[key] = st.slider(
            labels[key],
            min_value=0.0,
            max_value=1.0,
            value=float(preset[key]),
            step=0.05,
            key=f"scenario_{preset_name}_{key}",
        )

raw_sum = sum(raw_values.values())
if raw_sum <= 0:
    st.error("At least one factor must have a non-zero weight.")
    render_disclaimer()
    st.stop()

normalized = {key: value / raw_sum for key, value in raw_values.items()}
st.caption(
    "Weights are automatically normalized to sum to 1.00. "
    + " · ".join(f"{labels[k]} {v:.0%}" for k, v in normalized.items())
)

baseline = enrich_habitations(habitations_raw, weights=DEFAULT_WEIGHTS)
scenario = enrich_habitations(habitations_raw, weights=normalized)

comparison = baseline[
    ["habitation_id", "name", "population", "risk_score", "risk_level"]
].rename(columns={"risk_score": "baseline_score", "risk_level": "baseline_level"})
comparison = comparison.merge(
    scenario[["habitation_id", "risk_score", "risk_level"]].rename(
        columns={"risk_score": "scenario_score", "risk_level": "scenario_level"}
    ),
    on="habitation_id",
)
comparison["changed_class"] = comparison["baseline_level"] != comparison["scenario_level"]
comparison["score_change"] = comparison["scenario_score"] - comparison["baseline_score"]

changed = comparison[comparison["changed_class"]]
population_affected = int(changed["population"].sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Locations Changed Class", int(changed.shape[0]))
m2.metric("Population Affected", f"{population_affected:,}")
m3.metric(
    "Baseline Critical",
    int((comparison["baseline_level"] == "CRITICAL").sum()),
)
m4.metric(
    "Scenario Critical",
    int((comparison["scenario_level"] == "CRITICAL").sum()),
)

st.divider()
left, right = st.columns(2, gap="large")
with left:
    class_counts = pd.DataFrame(
        {
            "Risk Level": ["CRITICAL", "HIGH", "MODERATE", "LOW"],
            "Baseline": [
                int((comparison["baseline_level"] == level).sum())
                for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]
            ],
            "Scenario": [
                int((comparison["scenario_level"] == level).sum())
                for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]
            ],
        }
    ).melt(id_vars="Risk Level", var_name="Model", value_name="Habitations")
    fig = px.bar(
        class_counts,
        x="Risk Level",
        y="Habitations",
        color="Model",
        barmode="group",
        title="Risk-Class Distribution",
    )
    fig.update_layout(height=370, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, width="stretch")

with right:
    fig = px.scatter(
        comparison,
        x="baseline_score",
        y="scenario_score",
        hover_name="name",
        size="population",
        color="scenario_level",
        title="Baseline vs Scenario Risk Score",
        labels={"baseline_score": "Baseline Score", "scenario_score": "Scenario Score"},
    )
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(dash="dash"))
    fig.update_layout(height=370, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, width="stretch")

st.subheader("Locations most affected by the scenario")
st.dataframe(
    comparison.sort_values("score_change", key=lambda s: s.abs(), ascending=False)[
        [
            "name",
            "population",
            "baseline_score",
            "scenario_score",
            "score_change",
            "baseline_level",
            "scenario_level",
        ]
    ],
    width="stretch",
    hide_index=True,
)

render_disclaimer()
