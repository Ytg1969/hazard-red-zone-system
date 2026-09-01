import pandas as pd
import streamlit as st

from src.data_contracts import assess_habitation_dataset, assess_shelter_dataset
from src.live_operations import fetch_operations_snapshot
from src.provenance import default_provenance_register, source_health
from src.ui_theme import inject_global_css, render_data_mode_indicator, render_disclaimer, render_page_header

st.set_page_config(page_title="System Readiness", page_icon="OPS", layout="wide")
inject_global_css()
render_page_header(
    "System Readiness & Provenance",
    "Production-facing source health, freshness, provenance and deployment readiness for the SIH26191 decision-support platform.",
)

st.markdown("### Operational readiness")
left, right = st.columns([1.2, 1], gap="large")
with left:
    st.write(
        "This page makes the system's data confidence visible. LIVE, CACHED and DEMO sources are intentionally separated, "
        "and external context is not allowed to silently mutate the frozen evacuation-risk contract."
    )
with right:
    render_data_mode_indicator("LIVE")
    st.caption("LIVE here means the page can query external context; it does not mean every source is currently reachable.")

st.divider()
st.markdown("### Source health check")
city = st.selectbox("Operational location", ["Puri", "Guwahati", "Chennai"], index=0)
refresh = st.button("Run source health check", type="primary", width="stretch")

if refresh:
    with st.spinner("Checking live and official context sources..."):
        snapshot = fetch_operations_snapshot(city)
    rows = []
    for label, source in snapshot.get("sources", {}).items():
        health = source_health(source)
        rows.append({
            "Source": label,
            "Mode": health["mode"],
            "State": health["operational_state"],
            "Freshness": health["freshness"],
            "Age (min)": health["age_minutes"],
            "Access": health["access_status"] or "—",
            "Error": health["error"] or "—",
        })
    health_df = pd.DataFrame(rows)
    if health_df.empty:
        st.warning("No source-health rows were produced.")
    else:
        healthy = int((health_df["State"] == "HEALTHY").sum())
        degraded = int(health_df["State"].isin(["DEGRADED", "STALE"]).sum())
        demo_only = int((health_df["State"] == "DEMO_ONLY").sum())
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sources Checked", len(health_df))
        c2.metric("Healthy", healthy)
        c3.metric("Degraded / Stale", degraded)
        c4.metric("Demo-only", demo_only)
        st.dataframe(health_df, width="stretch", hide_index=True)
        st.caption("A source failure does not stop the deterministic red-zone, capacity or relocation pipeline.")
else:
    st.info("Run the health check to inspect current external-source availability and freshness.")

st.divider()
st.markdown("### Production dataset inspector")
st.caption(
    "Inspect candidate operational CSVs before they enter the analytical workflow. This does not certify a source as official; "
    "it checks schema integrity, provenance fields and carrying-capacity evidence completeness."
)
upload_left, upload_right = st.columns(2, gap="large")
with upload_left:
    habitation_upload = st.file_uploader("Inspect habitation CSV", type=["csv"], key="readiness_habitations")
    if habitation_upload is not None:
        try:
            habitation_df = pd.read_csv(habitation_upload)
            assessment = assess_habitation_dataset(habitation_df)
            if assessment["production_schema_valid"]:
                st.success(f"Schema valid · {assessment['rows']} row(s)")
            else:
                st.error("Schema/data integrity issues detected")
            st.json(assessment, expanded=False)
            if assessment["missing_provenance"]:
                st.warning("Missing recommended provenance fields: " + ", ".join(assessment["missing_provenance"]))
        except Exception as exc:
            st.error(f"Could not inspect habitation CSV: {exc}")

with upload_right:
    shelter_upload = st.file_uploader("Inspect shelter / relocation-site CSV", type=["csv"], key="readiness_shelters")
    if shelter_upload is not None:
        try:
            shelter_df = pd.read_csv(shelter_upload)
            assessment = assess_shelter_dataset(shelter_df)
            if assessment["production_schema_valid"]:
                st.success(f"Schema valid · resource evidence {assessment['resource_completeness_pct']:.0f}%")
            else:
                st.error("Schema/data integrity issues detected")
            st.json(assessment, expanded=False)
            if assessment["missing_resource_fields"]:
                st.warning("Missing carrying-capacity evidence: " + ", ".join(assessment["missing_resource_fields"]))
        except Exception as exc:
            st.error(f"Could not inspect shelter CSV: {exc}")

st.divider()
st.markdown("### Data provenance register")
provenance = pd.DataFrame(default_provenance_register())
provenance = provenance.rename(columns={
    "dataset": "Dataset",
    "source": "Source",
    "mode": "Expected Mode",
    "role": "Role",
    "affects_risk": "Affects Frozen Risk",
    "notes": "Operational Note",
})
st.dataframe(provenance, width="stretch", hide_index=True)

st.markdown("### Production gates")
gates = [
    ("Explainable baseline risk", "READY", "Frozen weighted risk formula and thresholds remain deterministic."),
    ("Shelter hard safety gate", "READY", "Unsafe/full shelters remain ineligible before ranking or optimization."),
    ("Capacity protection", "READY", "Shared capacity accounting prevents over-allocation."),
    ("Route provenance", "READY", "Local OSM → live OSRM → cached OSRM → straight-line fallback is explicit."),
    ("Live source isolation", "READY", "External context is CONTEXT_ONLY until source-specific calibration exists."),
    ("Authoritative national habitations", "PENDING", "Requires validated government production feeds or curated official datasets."),
    ("Bhuvan numeric calibration", "PENDING", "Layer classes, legend, reference period and 0–100 mapping must be validated."),
    ("IMD direct API access", "CONDITIONAL", "Official endpoint may require client/IP authorization."),
    ("NDMA SACHET production feed", "CONDITIONAL", "Requires a verified configured feed URL/identifier."),
]
for title, state, detail in gates:
    with st.container(border=True):
        a, b = st.columns([3, 1])
        with a:
            st.markdown(f"**{title}**")
            st.caption(detail)
        with b:
            st.markdown(f"**{state}**")

st.divider()
st.markdown("### Operational rule")
st.warning(
    "This platform provides evidence-backed decision support. It must not issue autonomous evacuation orders, "
    "and DEMO or uncalibrated context must never be presented as authoritative risk evidence."
)
render_disclaimer()
