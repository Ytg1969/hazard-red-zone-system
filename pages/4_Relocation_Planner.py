import pandas as pd
import plotly.express as px
import streamlit as st

from src.batch_relocation import plan_batch_relocation
from src.global_optimizer import optimize_relocation_flow
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.relocation import allocate_population, rank_shelters
from src.report_generator import generate_action_plan, generate_action_plan_pdf
from src.risk_engine import calculate_risk
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_demo_scope_controls,
    render_disclaimer,
    render_page_header,
    render_risk_badge,
)

st.set_page_config(page_title="Relocation Planner", layout="wide")
inject_global_css()
render_page_header("Relocation Planner", "Capacity-safe local shelter planning across realistic multi-city DEMO scenarios.")
render_data_mode_indicator("DEMO")
city, hazard_profile = render_demo_scope_controls("relocation")

try:
    habitations_raw, shelters_raw = load_demo_data(city)
    hazards = load_demo_hazards()
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards, hazard_type=hazard_profile)
    shelters = enrich_shelters(shelters_raw)
except Exception as exc:
    st.error(f"Unable to prepare relocation data: {exc}")
    render_disclaimer()
    st.stop()

st.markdown("### 1. Select affected habitation")
selected_name = st.selectbox("Habitation", habitations.sort_values("risk_score", ascending=False)["name"].tolist())
habitation = habitations[habitations["name"] == selected_name].iloc[0].to_dict()
local_shelters = shelters
if habitation.get("demo_city") and "demo_city" in shelters.columns:
    local_shelters = shelters[shelters["demo_city"] == habitation["demo_city"]].copy()
risk = calculate_risk(habitation)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Population", f"{int(habitation['population']):,}")
m2.metric("Risk Score", f"{risk['risk_score']:.1f}/100")
with m3:
    st.caption("Risk Level")
    render_risk_badge(risk["risk_level"])
m4.metric("Relocation Priority", habitation["relocation_priority"])
st.caption(f"Local shelter geography: **{habitation.get('demo_city','uploaded dataset')}** · Hazard profile: **{hazard_profile.title()}**")

st.markdown("### 2. Compare suitable shelters")
ranked = rank_shelters(habitation, local_shelters.to_dict(orient="records"))
if not ranked:
    st.error("No local shelter currently passes the safety and available-capacity filters.")
    render_disclaimer()
    st.stop()
ranked_df = pd.DataFrame(ranked)
st.dataframe(ranked_df[["shelter_name", "suitability_score", "distance_km", "safety_score", "accessibility_score", "available_capacity", "capacity_validation_status", "routing_mode"]], width="stretch", hide_index=True)

visual_left, visual_right = st.columns(2, gap="large")
with visual_left:
    st.bar_chart(ranked_df.head(6).set_index("shelter_name")["available_capacity"])
    st.caption("Available capacity after limiting-resource and occupancy constraints.")
with visual_right:
    fig = px.bar(ranked_df.head(5), x="shelter_name", y="suitability_score", title="Top Shelter Suitability Scores", labels={"shelter_name":"Shelter","suitability_score":"Suitability / 100"})
    st.plotly_chart(fig, width="stretch")

recommended = ranked[0]
st.markdown("### 3. Primary recommendation and population split")
left, right = st.columns([1, 1.35], gap="large")
with left:
    st.success(f"Recommended primary shelter: {recommended['shelter_name']}")
    st.metric("Suitability", f"{recommended['suitability_score']:.1f}/100")
    st.metric("Distance", f"{recommended['distance_km']:.2f} km")
    st.metric("Available Capacity", f"{int(recommended['available_capacity']):,}")
    st.caption(f"Routing: {recommended['routing_mode']} · Capacity: {recommended['capacity_validation_status']}")
with right:
    allocation = allocate_population(habitation, local_shelters.to_dict(orient="records"))
    a1, a2, a3 = st.columns(3)
    a1.metric("Required", f"{allocation['required_population']:,}")
    a2.metric("Allocated", f"{allocation['allocated_population']:,}")
    a3.metric("Remaining Deficit", f"{allocation['remaining_deficit']:,}")
    if allocation["allocations"]:
        st.dataframe(pd.DataFrame(allocation["allocations"]), width="stretch", hide_index=True)
    if allocation["remaining_deficit"] > 0:
        st.warning("Local safe-shelter capacity is insufficient; the deficit is preserved rather than overfilling a shelter.")
    else:
        st.success("The current local safe-shelter set can accommodate the full habitation population.")

st.markdown("### 4. System-wide priority allocation")
st.caption("Capacity is shared across priority habitations and constrained to the same demo city where city metadata exists, preventing double-booking and cross-state demo assignments.")
batch = plan_batch_relocation(habitations, shelters)
b1, b2, b3 = st.columns(3)
b1.metric("Priority Population", f"{batch['required_population']:,}")
b2.metric("Batch Allocated", f"{batch['allocated_population']:,}")
b3.metric("Batch Deficit", f"{batch['remaining_deficit']:,}")
if batch["allocations"]:
    st.dataframe(pd.DataFrame(batch["allocations"]), width="stretch", hide_index=True)
if batch["unallocated"]:
    st.warning("The batch plan reports an explicit deficit rather than reusing or overfilling committed shelter capacity.")
    st.dataframe(pd.DataFrame(batch["unallocated"]), width="stretch", hide_index=True)

with st.expander("Experimental global optimization comparison", expanded=False):
    st.caption("Network-simplex comparison uses only shelter candidates that already pass the normal safety/capacity gate. It is not an autonomous evacuation decision.")
    optimized = optimize_relocation_flow(habitations, shelters)
    o1, o2, o3 = st.columns(3)
    o1.metric("Required", f"{optimized['required_population']:,}")
    o2.metric("Globally Allocated", f"{optimized['allocated_population']:,}")
    o3.metric("Deficit", f"{optimized['remaining_deficit']:,}")
    if optimized["allocations"]:
        st.dataframe(pd.DataFrame(optimized["allocations"]), width="stretch", hide_index=True)
    st.caption(optimized.get("note", ""))

st.markdown("### 5. Draft administrative action plan")
action_plan = generate_action_plan(habitation=habitation, risk=risk, relocation=recommended, allocation=allocation, data_mode="DEMO")
pdf_plan = generate_action_plan_pdf(habitation=habitation, risk=risk, relocation=recommended, allocation=allocation, data_mode="DEMO")
export_left, export_right = st.columns(2)
with export_left:
    st.download_button("Download Action Plan (Markdown)", action_plan, f"{habitation['habitation_id']}_draft_action_plan.md", "text/markdown", width="stretch")
with export_right:
    st.download_button("Download Action Plan (PDF)", pdf_plan, f"{habitation['habitation_id']}_draft_action_plan.pdf", "application/pdf", width="stretch")
with st.expander("Preview action plan"):
    st.markdown(action_plan)
render_disclaimer()
