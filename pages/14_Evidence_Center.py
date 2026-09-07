from __future__ import annotations

import streamlit as st

from src.runtime_mode import offline_mode
from src.ui_theme import inject_global_css, render_disclaimer, render_page_header, render_source_card

st.set_page_config(page_title="Evidence Center", page_icon="EV", layout="wide", initial_sidebar_state="auto")
inject_global_css()
render_page_header(
    "Evidence Center",
    "Technical provenance, calibration and readiness tools collected in one secondary workspace instead of competing with the operator flow.",
)

if offline_mode():
    st.info("Offline field mode is active. Network-dependent source inspection remains unavailable; local evidence and readiness tools are still accessible.")

st.markdown("## Data & provenance")
left, mid, right = st.columns(3, gap="large")
with left:
    render_source_card("Operational data", "Load & validate", "Manage habitation, shelter and hazard datasets while preserving provenance and unknown values.")
    st.page_link("pages/9_Operational_Data.py", label="Open data workspace →")
with mid:
    render_source_card("GIS evidence", "Inspect sources", "Review source metadata, layer coverage, CRS, legend and calibration readiness.")
    st.page_link("pages/10_GIS_Source_Inspector.py", label="Open GIS inspector →")
with right:
    render_source_card("Schema mapping", "Validate contracts", "Map incoming columns to required analytical fields without fabricating missing operational values.")
    st.page_link("pages/12_Schema_Mapper.py", label="Open schema mapper →")

st.markdown("## Model & readiness")
left, mid, right = st.columns(3, gap="large")
with left:
    render_source_card("Hazard calibration", "Source-specific only", "Review calibrated hazard-source contracts. Uncalibrated live context never changes baseline risk.")
    st.page_link("pages/11_Calibrated_Hazard_Source.py", label="Open calibration →")
with mid:
    render_source_card("System readiness", "Field preflight", "Check offline assets, environment state and release-readiness diagnostics.")
    st.page_link("pages/8_System_Readiness.py", label="Open readiness →")
with right:
    render_source_card("Method", "Explainable model", "Inspect the frozen risk equation, thresholds, assumptions and decision-support boundaries.")
    st.page_link("pages/6_Methodology.py", label="Open methodology →")

st.markdown("## Scenario testing")
render_source_card(
    "Scenario Studio",
    "What-if analysis",
    "Explore controlled analytical scenarios without presenting hypothetical values as live operational truth.",
)
st.page_link("pages/5_Scenario_Studio.py", label="Open Scenario Studio →")

render_disclaimer()
