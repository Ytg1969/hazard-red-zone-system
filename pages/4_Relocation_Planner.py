import pandas as pd
import streamlit as st

from src.pipeline import (
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
)
from src.relocation import allocate_population, rank_shelters
from src.report_generator import generate_action_plan
from src.risk_engine import calculate_risk
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(page_title="Relocation Planner", layout="wide")
inject_global_css()
render_page_header(
    "Relocation Planner",
    "Select an affected habitation, compare safe shelters, review capacity and produce a draft action plan.",
)
render_data_mode_indicator("DEMO")

try:
    habitations_raw, shelters_raw = load_demo_data()
    try:
        hazards = load_demo_hazards()
    except Exception:
        hazards = None
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards)
    shelters = enrich_shelters(shelters_raw)
except Exception:
    st.error("Unable to prepare the relocation-planning demonstration data.")
    render_disclaimer()
    st.stop()

st.markdown("### 1. Select affected habitation")
selected_name = st.selectbox(
    "Habitation",
    habitations.sort_values("risk_score", ascending=False)["name"].tolist(),
)
habitation = habitations[habitations["name"] == selected_name].iloc[0].to_dict()
risk = calculate_risk(habitation)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Population", f"{int(habitation['population']):,}")
m2.metric("Risk Score", f"{risk['risk_score']:.1f}/100")
with m3:
    st.caption("Risk Level")
    render_risk_badge(risk["risk_level"])
m4.metric("Relocation Priority", habitation["relocation_priority"])

if habitation.get("inside_hazard_zone") is True:
    st.warning("This habitation intersects the active demonstration hazard footprint and should not be matched to a site solely on geographic proximity.")

st.markdown("### 2. Compare suitable shelters")
ranked = rank_shelters(habitation, shelters.to_dict(orient="records"))
if not ranked:
    st.error("No shelter currently passes the safety and available-capacity filters.")
    render_disclaimer()
    st.stop()

ranked_df = pd.DataFrame(ranked)
st.dataframe(
    ranked_df[
        [
            "shelter_name",
            "suitability_score",
            "distance_km",
            "safety_score",
            "accessibility_score",
            "available_capacity",
            "capacity_validation_status",
            "routing_mode",
        ]
    ],
    width="stretch",
    hide_index=True,
    column_config={
        "shelter_name": "Shelter",
        "suitability_score": st.column_config.NumberColumn("Suitability", format="%.1f"),
        "distance_km": st.column_config.NumberColumn("Distance (km)", format="%.2f"),
        "safety_score": st.column_config.NumberColumn("Safety", format="%.1f"),
        "accessibility_score": st.column_config.NumberColumn("Accessibility", format="%.1f"),
        "available_capacity": st.column_config.NumberColumn("Available Capacity", format="%.0f"),
        "capacity_validation_status": "Capacity Status",
        "routing_mode": "Routing Mode",
    },
)

recommended = ranked[0]
st.markdown("### 3. Primary recommendation and capacity allocation")
left, right = st.columns([1, 1.35], gap="large")
with left:
    st.success(f"Recommended primary shelter: {recommended['shelter_name']}")
    st.metric("Suitability Score", f"{recommended['suitability_score']:.1f}/100")
    st.metric("Distance", f"{recommended['distance_km']:.2f} km")
    if recommended.get("travel_time_min") is not None:
        st.metric("Estimated Travel Time", f"{recommended['travel_time_min']:.0f} min")
    st.metric("Available Capacity", f"{int(recommended['available_capacity']):,}")
    st.caption(
        f"Routing mode: {recommended['routing_mode']} | Capacity status: {recommended['capacity_validation_status']}"
    )

with right:
    allocation = allocate_population(habitation, shelters.to_dict(orient="records"))
    a1, a2, a3 = st.columns(3)
    a1.metric("Required", f"{allocation['required_population']:,}")
    a2.metric("Allocated", f"{allocation['allocated_population']:,}")
    a3.metric("Remaining Deficit", f"{allocation['remaining_deficit']:,}")
    if allocation["allocations"]:
        st.dataframe(
            pd.DataFrame(allocation["allocations"]),
            width="stretch",
            hide_index=True,
        )
    if allocation["remaining_deficit"] > 0:
        st.warning(
            "Current safe-shelter capacity is insufficient for the full habitation population. "
            "Additional sites or staged movement are required."
        )
    else:
        st.success("The current ranked shelter set can accommodate the full habitation population.")

st.markdown("### 4. Draft administrative action plan")
action_plan = generate_action_plan(
    habitation=habitation,
    risk=risk,
    relocation=recommended,
    allocation=allocation,
    data_mode="DEMO",
)
st.download_button(
    "Download Draft Action Plan",
    data=action_plan,
    file_name=f"{habitation['habitation_id']}_draft_action_plan.md",
    mime="text/markdown",
    width="stretch",
)
with st.expander("Preview action plan"):
    st.markdown(action_plan)

render_disclaimer()
