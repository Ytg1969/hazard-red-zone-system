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
use_live_routing = st.checkbox(
    "Use live OSRM road distance when a local cached road graph is unavailable",
    value=False,
    help="Road routing improves distance/travel-time evidence but does not include live traffic, road closures or hazard avoidance. If unavailable, the planner falls back visibly to cached/straight-line distance.",
)
ranked = rank_shelters(
    habitation,
    local_shelters.to_dict(orient="records"),
    allow_live_routing=use_live_routing,
)
if not ranked:
    st.error("No relocation site currently passes the safety and available-capacity gates.")
    render_disclaimer()
    st.stop()
ranked_df = pd.DataFrame(ranked)
show_cols = [c for c in [
    "shelter_name",
    "suitability_score",
    "distance_km",
    "travel_time_min",
    "route_status",
    "routing_mode",
    "safety_score",
    "accessibility_score",
    "available_capacity",
    "limiting_resource_label",
    "capacity_evidence_completeness_pct",
    "capacity_utilization_pct",
    "capacity_validation_status",
] if c in ranked_df.columns]
st.dataframe(ranked_df[show_cols], width="stretch", hide_index=True)

road_modes = {"cached_osm_graph", "osrm_live", "osrm_cached"}
road_candidate_count = sum(1 for item in ranked if item.get("routing_mode") in road_modes)
if road_candidate_count:
    st.success(f"Road-network distance available for {road_candidate_count} of {len(ranked)} qualified site(s).")
else:
    st.warning("No road-network route is active for the qualified sites; current ranking uses explicit straight-line fallback distance.")

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
    primary_metrics = st.columns(2)
    primary_metrics[0].metric("Suitability", f"{recommended['suitability_score']:.1f}/100")
    primary_metrics[1].metric("Distance", f"{recommended['distance_km']:.2f} km")
    primary_metrics[0].metric("Available Capacity", f"{int(recommended['available_capacity']):,}")
    primary_metrics[1].metric("Capacity Use", f"{recommended.get('capacity_utilization_pct', 0):.1f}%")
    travel_time = recommended.get("travel_time_min")
    if travel_time is not None:
        st.metric("Estimated Road Travel Time", f"{float(travel_time):.1f} min")
    st.caption(
        f"Route provenance: **{recommended.get('routing_mode', 'unknown')}** · "
        f"{recommended.get('route_status', 'UNKNOWN')}"
    )
    route_note = str(recommended.get("route_note") or "").strip()
    if route_note:
        st.caption(route_note)
    if recommended.get("route_stale"):
        st.warning("The selected route is using cached routing data because the latest live refresh was unavailable.")
    st.caption(
        f"Capacity evidence: **{recommended['capacity_validation_status']}** · "
        f"{recommended.get('capacity_evidence_completeness_pct', 0):.1f}% resource evidence complete"
    )
    st.info(
        f"Current limiting factor: **{recommended.get('limiting_resource_label', 'Unknown')}** "
        f"at **{int(float(recommended.get('limiting_capacity', recommended['effective_capacity']))):,} people**."
    )
    missing = recommended.get("missing_resource_fields") or []
    if missing:
        st.warning("Missing capacity evidence: " + ", ".join(str(value).replace("_capacity", "").replace("_", " ").title() for value in missing))
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

with st.expander("Carrying-capacity evidence across qualified sites", expanded=False):
    evidence_cols = [c for c in [
        "shelter_name",
        "effective_capacity",
        "available_capacity",
        "limiting_resource_label",
        "limiting_capacity",
        "capacity_utilization_pct",
        "capacity_evidence_completeness_pct",
        "capacity_validation_status",
    ] if c in ranked_df.columns]
    st.dataframe(ranked_df[evidence_cols], width="stretch", hide_index=True)
    st.caption(
        "VALIDATED means water, sanitation and access/logistics sub-capacities are all known. "
        "PARTIAL uses the minimum known constraint. UNVALIDATED falls back to total physical capacity. Unknown evidence is never treated as zero."
    )

with st.expander("Route provenance across qualified sites", expanded=False):
    route_cols = [c for c in [
        "shelter_name", "distance_km", "travel_time_min", "routing_mode", "route_status", "route_stale", "route_note"
    ] if c in ranked_df.columns]
    st.dataframe(ranked_df[route_cols].astype(str), width="stretch", hide_index=True)
    st.caption("Routing is advisory. The system currently does not claim live traffic, road-closure awareness or hazard-avoiding routing.")

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