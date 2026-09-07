import pandas as pd
import streamlit as st

from src.batch_relocation import plan_batch_relocation
from src.global_optimizer import optimize_relocation_flow
from src.operational_hazards import geojson_to_gdf
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards
from src.relocation import allocate_population, rank_shelters
from src.report_generator import generate_action_plan, generate_action_plan_pdf
from src.risk_engine import calculate_risk
from src.runtime_mode import offline_mode
from src.streamlit_workspace import resolve_operational_hazard, resolve_operational_workspace
from src.ui_theme import (
    inject_global_css,
    render_command_card,
    render_context_bar,
    render_data_mode_indicator,
    render_decision_gate,
    render_demo_scope_controls,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
    render_risk_badge,
    render_section_header,
    render_source_card,
)

st.set_page_config(page_title="Relocation", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
render_page_header(
    "Relocation",
    "Validate whether the selected population can move into safe, available capacity without overbooking shared shelters.",
)

is_offline = offline_mode()
resolved = None
try:
    resolved = resolve_operational_workspace(auto_configured=True)
except Exception as exc:
    st.warning(f"Configured operational feeds are unavailable: {exc}")

operational = bool(resolved)
hazard_source = None
if operational:
    workspace = resolved["payload"]
    mode = str(workspace.get("habitation_mode", "UNVERIFIED")).upper()
    area_label = str(workspace.get("label", "Operational area"))
    habitations_raw = resolved["habitations"]
    shelters_raw = resolved["shelters"]
    with st.sidebar:
        st.markdown("### Planning context")
        hazard_profile = st.selectbox(
            "Hazard profile",
            ["stored", "combined", "flood", "cyclone", "landslide", "earthquake", "drought"],
            index=0,
            format_func=lambda v: "Stored / calibrated GIS" if v == "stored" else v.title(),
        )
        st.success(f"Scope: {area_label}")
    hazard_data = None
    if hazard_profile == "stored":
        try:
            hazard_source = resolve_operational_hazard(auto_configured=True)
            if hazard_source:
                hazard_data = geojson_to_gdf(hazard_source["geojson"])
        except Exception as exc:
            st.error(f"Configured operational hazard layer could not be loaded: {exc}")
            st.stop()
else:
    workspace = None
    mode = "DEMO"
    city, hazard_profile = render_demo_scope_controls("relocation")
    area_label = city
    habitations_raw, shelters_raw = load_demo_data(city)
    hazard_data = load_demo_hazards()

try:
    habitations = enrich_habitations(
        habitations_raw,
        hazard_data=hazard_data,
        hazard_type=hazard_profile,
        add_coordination_zones=not operational,
    )
    shelters = enrich_shelters(shelters_raw)
except Exception as exc:
    st.error(f"Unable to prepare relocation data: {exc}")
    render_disclaimer()
    st.stop()

ordered = habitations.sort_values("risk_score", ascending=False)
priority_names = ordered["name"].astype(str).tolist()
remembered = st.session_state.get("focus_location")
default_index = priority_names.index(remembered) if remembered in priority_names else 0
with st.sidebar:
    st.markdown("### Affected location")
    selected_name = st.selectbox("Location", priority_names, index=default_index, key="relocation_focus")
    with st.expander("Routing", expanded=False):
        use_live_routing = st.checkbox(
            "Use live OSRM if cached road data is unavailable",
            value=False,
            disabled=is_offline,
            help="Routing is advisory and never overrides shelter safety/capacity gates.",
        )
        if is_offline:
            st.caption("Offline mode uses configured/cached routing when available and otherwise shows explicit fallback distance.")
st.session_state["focus_location"] = selected_name
habitation = habitations[habitations["name"].astype(str) == str(selected_name)].iloc[0].to_dict()
risk = calculate_risk(habitation)

local_shelters = shelters
if not operational and habitation.get("demo_city") and "demo_city" in shelters.columns:
    local_shelters = shelters[shelters["demo_city"] == habitation["demo_city"]].copy()

data_mode = workspace.get("habitation_mode", "UNVERIFIED") if operational else "DEMO"
if data_mode not in {"LIVE", "CACHED", "DEMO"}:
    data_mode = "DEMO"

ranked = rank_shelters(
    habitation,
    local_shelters.to_dict(orient="records"),
    allow_live_routing=use_live_routing,
)
allocation = allocate_population(habitation, local_shelters.to_dict(orient="records"))
required = int(allocation["required_population"])
allocated = int(allocation["allocated_population"])
deficit = int(allocation["remaining_deficit"])
coverage = 100.0 if required <= 0 else min(100.0, allocated / required * 100.0)

render_context_bar(
    str(area_label),
    f"{hazard_profile.replace('_', ' ').title()} · {mode}",
    "SAFETY + CAPACITY HARD GATES",
)
if mode in {"LIVE", "CACHED", "DEMO"}:
    render_data_mode_indicator(mode)
else:
    st.warning("Operational workspace provenance is UNVERIFIED.")

render_kpi_strip([
    ("Affected population", f"{int(habitation['population']):,}", habitation["name"]),
    ("Risk", f"{risk['risk_score']:.1f}/100", risk["risk_level"]),
    ("Required move", f"{required:,}", "Population requiring allocation"),
    ("Safe allocation", f"{allocated:,}", f"{coverage:.0f}% covered"),
    ("Remaining Deficit", f"{deficit:,}", "Explicit unmet safe capacity" if deficit else "Current qualified capacity covers demand"),
])

render_section_header(
    "Decision gate",
    "The planner rejects unsafe or full shelters before ranking and never fills beyond available capacity.",
    "CAN EVERYONE MOVE?",
)
status_left, status_right = st.columns([1.7, 1], gap="large")
with status_left:
    answer = "Capacity shortfall" if deficit else "Safe capacity available"
    detail = (
        f"Qualified shelters can absorb {allocated:,} of {required:,} people. {deficit:,} remain without verified safe capacity."
        if deficit
        else f"All {required:,} people can be allocated across the current qualified shelter set without exceeding available capacity."
    )
    render_command_card(
        "Relocation decision",
        answer,
        detail,
        severity="critical" if deficit else "",
    )
    st.progress(max(0.0, min(1.0, coverage / 100.0)), text=f"Safe allocation coverage {coverage:.0f}%")
    if deficit:
        st.error("Additional verified safe capacity is required; the system will not hide the deficit or overfill a shelter.")
    else:
        st.success("Current qualified capacity covers the selected population under the present analytical inputs.")
with status_right:
    render_risk_badge(risk["risk_level"])
    render_decision_gate(
        "Shelter safety gate",
        "Only shelters meeting the minimum safety threshold enter the recommendation set.",
        "ok",
    )
    render_decision_gate(
        "Capacity ledger",
        f"{allocated:,}/{required:,} people currently allocated",
        "danger" if deficit else "ok",
    )
    st.page_link("pages/2_Red_Zone_Map.py", label="◉  Review route on map", use_container_width=True)

if not ranked:
    st.error("No relocation site currently passes the safety and available-capacity gates.")
    st.page_link("pages/13_Briefing.py", label="▤  Open incident briefing", use_container_width=True)
    render_disclaimer()
    st.stop()

ranked_df = pd.DataFrame(ranked)
recommended = ranked[0]
travel_time = recommended.get("travel_time_min")

render_section_header(
    "Primary destination",
    "The top-ranked qualified shelter remains a recommendation, not an automated order.",
    "QUALIFIED SITE #1",
)
recommendation_left, allocation_right = st.columns([1.18, 1], gap="large")
with recommendation_left:
    render_source_card(
        recommended["shelter_name"],
        f"{recommended['suitability_score']:.1f}/100 suitability",
        f"Safety {float(recommended.get('safety_score', 0)):.0f}/100 · {int(recommended['available_capacity']):,} places available",
    )
    recommendation_metrics = [
        ("Suitability", f"{recommended['suitability_score']:.1f}/100", "Qualified-site score"),
        ("Distance", f"{recommended['distance_km']:.2f} km", str(recommended.get("routing_mode", "unknown"))),
        ("Available capacity", f"{int(recommended['available_capacity']):,}", "After occupancy/resource constraints"),
        ("Safety", f"{float(recommended.get('safety_score', 0)):.0f}/100", str(recommended.get("capacity_validation_status", "UNKNOWN"))),
    ]
    if travel_time is not None:
        recommendation_metrics.append(
            ("Travel estimate", f"{float(travel_time):.1f} min", str(recommended.get("route_status", "UNKNOWN")))
        )
    render_kpi_strip(recommendation_metrics)
    limiting_label = recommended.get("limiting_resource_label", "Unknown")
    limiting_capacity = int(float(recommended.get("limiting_capacity", recommended.get("effective_capacity", 0)) or 0))
    render_decision_gate(
        "Limiting resource",
        f"{limiting_label} currently caps usable capacity at {limiting_capacity:,} people.",
        "warn" if recommended.get("capacity_evidence_completeness_pct", 0) < 100 else "ok",
    )
    route_note = str(recommended.get("route_note") or "").strip()
    if route_note:
        st.caption(route_note)
    if recommended.get("route_stale"):
        st.warning("This route uses cached routing data because a fresher route was unavailable.")

with allocation_right:
    st.markdown("#### Allocation ledger")
    render_kpi_strip([
        ("Required", f"{required:,}", "Selected location"),
        ("Allocated", f"{allocated:,}", "Across qualified sites"),
        ("Remaining Deficit", f"{deficit:,}", "Never hidden or overfilled"),
    ])
    if allocation["allocations"]:
        st.dataframe(pd.DataFrame(allocation["allocations"]), width="stretch", hide_index=True)

render_section_header(
    "Qualified shortlist",
    "Only candidates that already passed safety and available-capacity gates appear here.",
    f"{len(ranked)} SITES",
)
short_cols = [
    column
    for column in [
        "shelter_name",
        "suitability_score",
        "distance_km",
        "travel_time_min",
        "available_capacity",
        "safety_score",
        "limiting_resource_label",
        "route_status",
    ]
    if column in ranked_df.columns
]
st.dataframe(
    ranked_df[short_cols].head(8),
    width="stretch",
    hide_index=True,
    column_config={
        "suitability_score": st.column_config.ProgressColumn("Suitability", min_value=0, max_value=100, format="%.1f"),
        "available_capacity": st.column_config.NumberColumn("Available", format=",%d"),
        "distance_km": st.column_config.NumberColumn("Distance km", format="%.2f"),
    },
)

road_modes = {"cached_osm_graph", "osrm_live", "osrm_cached"}
road_candidate_count = sum(1 for item in ranked if item.get("routing_mode") in road_modes)
if road_candidate_count:
    st.caption(f"Road-network distance is available for {road_candidate_count} of {len(ranked)} qualified site(s).")
else:
    st.warning("Qualified sites currently use explicit straight-line fallback distance; no road-network route is active.")

with st.expander("Site evidence & route provenance", expanded=False):
    detail_cols = [
        column
        for column in [
            "shelter_name",
            "suitability_score",
            "safety_score",
            "accessibility_score",
            "effective_capacity",
            "available_capacity",
            "limiting_resource_label",
            "limiting_capacity",
            "capacity_evidence_completeness_pct",
            "capacity_validation_status",
            "distance_km",
            "travel_time_min",
            "routing_mode",
            "route_status",
            "route_stale",
            "route_note",
        ]
        if column in ranked_df.columns
    ]
    st.dataframe(ranked_df[detail_cols].astype(str), width="stretch", hide_index=True)
    st.caption("Routing is advisory. No live traffic, closure or hazard-avoidance claim is made without a verified source.")

render_section_header(
    "Shared incident capacity",
    "Check the whole priority population against one shared shelter ledger to prevent double booking.",
    "BATCH PLAN",
)
batch = plan_batch_relocation(habitations, shelters)
render_kpi_strip([
    ("Priority population", f"{batch['required_population']:,}", "Included in shared plan"),
    ("Batch allocated", f"{batch['allocated_population']:,}", "One shared capacity ledger"),
    ("Batch Deficit", f"{batch['remaining_deficit']:,}", "Explicit unmet capacity"),
])
if batch["allocations"]:
    with st.expander("Shared allocation register", expanded=False):
        st.dataframe(pd.DataFrame(batch["allocations"]), width="stretch", hide_index=True)
if batch["unallocated"]:
    st.warning("The shared plan contains an explicit capacity deficit; shelters are not double-booked.")

with st.expander("Advanced optimization comparison", expanded=False):
    optimized = optimize_relocation_flow(habitations, shelters)
    render_kpi_strip([
        ("Required", f"{optimized['required_population']:,}", "Priority population"),
        ("Optimized allocation", f"{optimized['allocated_population']:,}", "Qualified candidates only"),
        ("Deficit", f"{optimized['remaining_deficit']:,}", "Unmet qualified capacity"),
    ])
    if optimized["allocations"]:
        st.dataframe(pd.DataFrame(optimized["allocations"]), width="stretch", hide_index=True)
    st.caption(optimized.get("note", ""))

render_section_header(
    "Operator export",
    "Generate a reviewable draft action plan after the risk, shelter and route evidence have been inspected.",
    "NOT AN EVACUATION ORDER",
)
report_provenance = dict((workspace or {}).get("provenance") or {})
if operational and hazard_source:
    report_provenance["hazard"] = {
        "label": hazard_source.get("label", "Calibrated hazard GeoJSON"),
        "mode": hazard_source.get("mode", "SESSION"),
        "calibration_status": "Explicitly activated calibrated hazard source",
    }

action_plan = generate_action_plan(
    habitation=habitation,
    risk=risk,
    relocation=recommended,
    allocation=allocation,
    data_mode=data_mode,
    provenance=report_provenance or None,
)

pdf_plan = None
pdf_error = None
try:
    generated_pdf = generate_action_plan_pdf(
        habitation=habitation,
        risk=risk,
        relocation=recommended,
        allocation=allocation,
        data_mode=data_mode,
        provenance=report_provenance or None,
    )
    if not isinstance(generated_pdf, (bytes, bytearray)):
        raise TypeError("PDF generator did not return binary data")
    pdf_plan = bytes(generated_pdf)
    if len(pdf_plan) < 100 or not pdf_plan.startswith(b"%PDF"):
        raise ValueError("Generated file is not a valid PDF payload")
except Exception as exc:
    pdf_error = str(exc)

export_left, export_mid, export_right = st.columns(3, gap="small")
with export_left:
    st.download_button(
        "Download Markdown",
        data=action_plan.encode("utf-8"),
        file_name=f"{habitation['habitation_id']}_draft_action_plan.md",
        mime="text/markdown; charset=utf-8",
        use_container_width=True,
        key=f"markdown_download_{habitation['habitation_id']}",
    )
with export_mid:
    if pdf_plan is not None:
        st.download_button(
            "Download PDF",
            data=pdf_plan,
            file_name=f"{habitation['habitation_id']}_draft_action_plan.pdf",
            mime="application/pdf",
            use_container_width=True,
            key=f"pdf_download_{habitation['habitation_id']}",
        )
    else:
        st.button("PDF unavailable", disabled=True, use_container_width=True)
        if pdf_error:
            st.caption(pdf_error)
with export_right:
    st.page_link("pages/13_Briefing.py", label="▤  Open incident briefing", use_container_width=True)

render_disclaimer()
