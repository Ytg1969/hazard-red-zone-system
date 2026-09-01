import pandas as pd
import plotly.express as px
import streamlit as st

from src.operational_hazards import geojson_to_gdf
from src.pipeline import enrich_habitations, load_demo_data, load_demo_hazards
from src.risk_engine import DEFAULT_WEIGHTS
from src.streamlit_workspace import resolve_operational_workspace
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_demo_scope_controls, render_disclaimer, render_page_header

st.set_page_config(page_title="Scenario Studio", layout="wide")
inject_global_css()
render_page_header("Scenario Studio", "Test policy-weight sensitivity without changing the frozen baseline risk model or silently mutating live evidence.")

resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds are unavailable: {exc}")

if resolved:
    payload = resolved["payload"]
    habitations_raw = resolved["habitations"]
    active_label = str(payload.get("label", "Operational dataset"))
    mode = str(payload.get("habitation_mode", "UNVERIFIED"))
    with st.sidebar:
        st.success(f"Operational workspace: {active_label}")
        hazard_profile = st.selectbox(
            "Analytical hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda value: "Stored / calibrated GIS" if value == "stored" else value.title(),
            key="scenario_operational_hazard",
        )
        st.page_link("pages/9_Operational_Data.py", label="Manage Operational Data", use_container_width=True)
    if mode in {"LIVE", "CACHED", "DEMO"}:
        render_data_mode_indicator(mode)
    else:
        st.warning("Operational data provenance is UNVERIFIED.")
    hazards = None
    if hazard_profile == "stored" and st.session_state.get("operational_hazard_geojson"):
        try:
            hazards = geojson_to_gdf(st.session_state["operational_hazard_geojson"])
        except Exception as exc:
            st.warning(f"Active calibrated hazard layer could not be loaded: {exc}")
    context_caption = f"Operational geography: **{active_label}** · {hazard_profile.title()}"
else:
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("scenario")
    habitations_raw, _ = load_demo_data(city)
    try:
        hazards = load_demo_hazards()
    except Exception:
        hazards = None
    context_caption = f"Fallback DEMO geography: **{city}** · {hazard_profile.title()}"

PRESETS = {
    "Recommended / Balanced": DEFAULT_WEIGHTS,
    "Hazard Priority": {"hazard": 0.50, "exposure": 0.20, "vulnerability": 0.15, "accessibility": 0.15},
    "Vulnerability Priority": {"hazard": 0.25, "exposure": 0.20, "vulnerability": 0.40, "accessibility": 0.15},
    "Evacuation Access Priority": {"hazard": 0.25, "exposure": 0.20, "vulnerability": 0.20, "accessibility": 0.35},
}
preset_name = st.selectbox("Scenario preset", list(PRESETS))
preset = PRESETS[preset_name]
st.caption(context_caption + " · baseline and scenario use the same hazard evidence so only policy-weight sensitivity changes.")

st.markdown("### Risk factor emphasis")
cols = st.columns(4)
raw_values = {}
labels = {"hazard": "Hazard", "exposure": "Exposure", "vulnerability": "Vulnerability", "accessibility": "Evacuation Difficulty"}
for col, key in zip(cols, ["hazard", "exposure", "vulnerability", "accessibility"]):
    with col:
        raw_values[key] = st.slider(labels[key], 0.0, 1.0, float(preset[key]), 0.05, key=f"scenario_{preset_name}_{key}")
raw_sum = sum(raw_values.values())
if raw_sum <= 0:
    st.error("At least one factor must have a non-zero weight.")
    render_disclaimer()
    st.stop()
normalized = {key: value / raw_sum for key, value in raw_values.items()}
st.caption("Scenario weights are automatically normalized to 1.00: " + " · ".join(f"{labels[k]} {v:.0%}" for k, v in normalized.items()))
st.info("These scenario weights are sensitivity-analysis controls only. The production baseline remains 0.35H + 0.25E + 0.25V + 0.15A.")

try:
    baseline = enrich_habitations(habitations_raw, weights=DEFAULT_WEIGHTS, hazard_data=hazards, hazard_type=hazard_profile, add_coordination_zones=False)
    scenario = enrich_habitations(habitations_raw, weights=normalized, hazard_data=hazards, hazard_type=hazard_profile, add_coordination_zones=False)
except Exception as exc:
    st.error(f"Unable to run the scenario: {exc}")
    st.caption("For operational data, use Stored/GIS unless the uploaded rows contain the indicator fields required by the selected named hazard profile.")
    render_disclaimer()
    st.stop()

comparison = baseline[["habitation_id", "name", "population", "risk_score", "risk_level"]].rename(columns={"risk_score": "baseline_score", "risk_level": "baseline_level"})
comparison = comparison.merge(scenario[["habitation_id", "risk_score", "risk_level"]].rename(columns={"risk_score": "scenario_score", "risk_level": "scenario_level"}), on="habitation_id")
comparison["changed_class"] = comparison["baseline_level"] != comparison["scenario_level"]
comparison["score_change"] = comparison["scenario_score"] - comparison["baseline_score"]
changed = comparison[comparison["changed_class"]]
population_affected = int(changed["population"].sum())

m1, m2, m3, m4 = st.columns(4)
m1.metric("Locations Changed Class", int(changed.shape[0]))
m2.metric("Population Affected", f"{population_affected:,}")
m3.metric("Baseline Critical", int((comparison["baseline_level"] == "CRITICAL").sum()))
m4.metric("Scenario Critical", int((comparison["scenario_level"] == "CRITICAL").sum()))

st.divider()
left, right = st.columns(2, gap="large")
with left:
    levels = ["CRITICAL", "HIGH", "MODERATE", "LOW"]
    class_counts = pd.DataFrame({
        "Risk Level": levels,
        "Baseline": [int((comparison["baseline_level"] == level).sum()) for level in levels],
        "Scenario": [int((comparison["scenario_level"] == level).sum()) for level in levels],
    }).melt(id_vars="Risk Level", var_name="Model", value_name="Habitations")
    st.plotly_chart(px.bar(class_counts, x="Risk Level", y="Habitations", color="Model", barmode="group", title="Risk-Class Distribution"), width="stretch")
with right:
    fig = px.scatter(comparison, x="baseline_score", y="scenario_score", hover_name="name", size="population", color="scenario_level", title="Baseline vs Scenario Risk Score")
    fig.add_shape(type="line", x0=0, y0=0, x1=100, y1=100, line=dict(dash="dash"))
    st.plotly_chart(fig, width="stretch")

st.subheader("Locations most affected by the scenario")
st.dataframe(
    comparison.sort_values("score_change", key=lambda s: s.abs(), ascending=False)[
        ["name", "population", "baseline_score", "scenario_score", "score_change", "baseline_level", "scenario_level"]
    ],
    width="stretch",
    hide_index=True,
)

if resolved:
    st.caption("Operational scenario results are analytical sensitivity outputs, not relocation orders or changes to the approved baseline policy weights.")
render_disclaimer()
