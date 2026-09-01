import pandas as pd
import plotly.express as px
import streamlit as st

from src.batch_relocation import plan_batch_relocation
from src.global_optimizer import optimize_relocation_flow
from src.operational_hazards import geojson_to_gdf
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.relocation import allocate_population, rank_shelters
from src.report_generator import generate_action_plan, generate_action_plan_pdf
from src.risk_engine import calculate_risk
from src.streamlit_workspace import resolve_operational_hazard, resolve_operational_workspace
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_demo_scope_controls, render_disclaimer, render_page_header, render_risk_badge

st.set_page_config(page_title="Relocation Planner", layout="wide")
inject_global_css()
render_page_header("Relocation Planner", "Capacity-safe relocation planning using the active operational workspace or the bundled fallback dataset.")

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
    shelters_raw = resolved["shelters"]
    hazard_profile = st.sidebar.selectbox("Analytical hazard profile", ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"], index=0, format_func=lambda v: "Stored / calibrated GIS" if v == "stored" else v.title())
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
    st.sidebar.page_link("pages/9_Operational_Data.py", label="Manage operational data")
else:
    workspace = None
    render_data_mode_indicator("DEMO")
    city, hazard_profile = render_demo_scope_controls("relocation")
    area_label = city
    habitations_raw, shelters_raw = load_demo_data(city)
    hazard_data = load_demo_hazards()

try:
    habitations = enrich_habitations(habitations_raw, hazard_data=hazard_data, hazard_type=hazard_profile, add_coordination_zones=not operational)
    shelters = enrich_shelters(shelters_raw)
except Exception as exc:
    st.error(f"Unable to prepare relocation data: {exc}")
    render_disclaimer()
    st.stop()

st.markdown("### 1 · Select affected habitation")
selected_name = st.selectbox("Habitation", habitations.sort_values("risk_score", ascending=False)["name"].tolist())
habitation = habitations[habitations["name"] == selected_name].iloc[0].to_dict()
local_shelters = shelters
if not operational and habitation.get("demo_city") and "demo_city" in shelters.columns:
    local_shelters = shelters[shelters["demo_city"] == habitation["demo_city"]].copy()
risk = calculate_risk(habitation)

data_mode = workspace.get("habitation_mode", "UNVERIFIED") if operational else "DEMO"
if data_mode not in {"LIVE", "CACHED", "DEMO"}:
    data_mode = "DEMO"

m1, m2, m3, m4 = st.columns(4)
m1.metric("Population", f"{int(habitation['population']):,}")
m2.metric("Risk Score", f"{risk['risk_score']:.1f}/100")
with m3:
    st.caption("Risk Level")
    render_risk_badge(risk["risk_level"])
m4.metric("Relocation Priority", habitation["relocation_priority"])
st.caption(f"Operational scope: **{area_label}** · Hazard profile: **{hazard_profile.replace('_', ' ').title()}**")
if operational and hazard_source:
    st.caption(f"Calibrated hazard source: **{hazard_source.get('label', 'GeoJSON')}** · {hazard_source.get('mode', 'SESSION')}")

st.markdown("### 2 · Compare safe relocation sites")
ranked = rank_shelters(habitation, local_shelters.to_dict(orient="records"))
if not ranked:
    st.error("No relocation site currently passes the safety and available-capacity gates.")
    render_disclaimer()
    st.stop()
ranked_df = pd.DataFrame(ranked)
show_cols = [c for c in ["shelter_name", "suitability_score", "distance_km", "safety_score", "accessibility_score", "available_capacity", "capacity_validation_status", "routing_mode"] if c in ranked_df.columns]
st.dataframe(ranked_df[show_cols], width="stretch", hide_index=True)

visual_left, visual_right = st.columns(2, gap="large")
with visual_left:
    st.bar_chart(ranked_df.head(6).set_index("shelter_name")["available_capacity"])
    st.caption("Available capacity after limiting-resource and occupancy constraints.")
with visual_right:
    fig = px.bar(ranked_df.head(5), x="shelter_name", y="suitability_score", title="Top relocation-site suitability", labels={"shelter_name": "Site", "suitability_score": "Suitability / 100"})
    st.plotly_chart(fig, width="stretch")

recommended = ranked[0]
st.markdown("### 3 · Primary recommendation and population split")
left, right = st.columns([1, 1.35], gap="large")
with left:
    st.success(f"Recommended primary site: {recommended['shelter_name']}")
    st.metric("Suitability", f"{recommended['suitability_score']:.1f}/100")
    st.metric("Distance", f"{recommended['distance_km']:.2f} km")
    st.metric("Available Capacity", f"{int(recommended['available_capacity']):,}")
    st.caption(f"Capacity evidence: {recommended['capacity_validation_status']}")
with right:
    allocation = allocate_population(habitation, local_shelters.to_dict(orient="records"))
    a1, a2, a3 = st.columns(3)
    a1.metric("Required", f"{allocation['required_population']:,}")
    a2.metric("Allocated", f"{allocation['allocated_population']:,}")
    a3.metric("Remaining Deficit", f"{allocation['remaining_deficit']:,}")
    if allocation["allocations"]:
        st.dataframe(pd.DataFrame(allocation["allocations"]), width="stretch", hide_index=True)
    if allocation["remaining_deficit"] > 0:
        st.warning("Safe capacity is insufficient; the deficit remains explicit rather than overfilling a site.")
    else:
        st.success("The current safe-site set can accommodate the full habitation population.")

st.markdown("### 4 · Shared-capacity allocation")
st.caption("All priority habitations share one capacity ledger. The planner never double-books capacity; demonstration city boundaries are used only in fallback mode.")
batch = plan_batch_relocation(habitations, shelters)
b1, b2, b3 = st.columns(3)
b1.metric("Priority Population", f"{batch['required_population']:,}")
b2.metric("Batch Allocated", f"{batch['allocated_population']:,}")
b3.metric("Batch Deficit", f"{batch['remaining_deficit']:,}")
if batch["allocations"]:
    st.dataframe(pd.DataFrame(batch["allocations"]), width="stretch", hide_index=True)
if batch["unallocated"]:
    st.warning("The batch plan preserves an explicit capacity deficit.")
    st.dataframe(pd.DataFrame(batch["unallocated"]), width="stretch", hide_index=True)

with st.expander("Experimental global optimization comparison", expanded=False):
    st.caption("Network-simplex only considers candidates that already pass safety/capacity gates. It is not an autonomous evacuation order.")
    optimized = optimize_relocation_flow(habitations, shelters)
    o1, o2, o3 = st.columns(3)
    o1.metric("Required", f"{optimized['required_population']:,}")
    o2.metric("Globally Allocated", f"{optimized['allocated_population']:,}")
    o3.metric("Deficit", f"{optimized['remaining_deficit']:,}")
    if optimized["allocations"]:
        st.dataframe(pd.DataFrame(optimized["allocations"]), width="stretch", hide_index=True)
    st.caption(optimized.get("note", ""))

st.markdown("### 5 · Draft administrative action plan")
action_plan = generate_action_plan(habitation=habitation, risk=risk, relocation=recommended, allocation=allocation, data_mode=data_mode)

pdf_plan = None
pdf_error = None
try:
    generated_pdf = generate_action_plan_pdf(habitation=habitation, risk=risk, relocation=recommended, allocation=allocation, data_mode=data_mode)
    if not isinstance(generated_pdf, (bytes, bytearray)):
        raise TypeError("PDF generator did not return binary data")
    pdf_plan = bytes(generated_pdf)
    if len(pdf_plan) < 100 or not pdf_plan.startswith(b"%PDF"):
        raise ValueError("Generated file is not a valid PDF payload")
except Exception as exc:
    pdf_error = str(exc)

export_left, export_right = st.columns(2)
with export_left:
    st.download_button("Download Action Plan (Markdown)", data=action_plan.encode("utf-8"), file_name=f"{habitation['habitation_id']}_draft_action_plan.md", mime="text/markdown; charset=utf-8", width="stretch", key=f"markdown_download_{habitation['habitation_id']}")
with export_right:
    if pdf_plan is not None:
        st.download_button("Download Action Plan (PDF)", data=pdf_plan, file_name=f"{habitation['habitation_id']}_draft_action_plan.pdf", mime="application/pdf", width="stretch", key=f"pdf_download_{habitation['habitation_id']}")
        st.caption(f"PDF ready · {len(pdf_plan) / 1024:.1f} KB")
    else:
        st.error("PDF export could not be generated on this runtime.")
        if pdf_error:
            st.caption(pdf_error)

with st.expander("Preview action plan"):
    st.markdown(action_plan)
render_disclaimer()
