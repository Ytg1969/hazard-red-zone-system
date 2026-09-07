from __future__ import annotations

import streamlit as st

from src.runtime_mode import offline_mode
from src.ui_theme import (
    inject_global_css,
    render_command_card,
    render_context_bar,
    render_decision_gate,
    render_disclaimer,
    render_page_header,
    render_section_header,
    render_source_card,
)

st.set_page_config(page_title="Evidence Center", page_icon="EV", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
render_page_header(
    "Evidence Center",
    "Secondary provenance, calibration and readiness tools kept outside the primary incident decision flow.",
)

render_context_bar(
    "Technical workspace",
    "Provenance · calibration · schema · readiness",
    "EVIDENCE ONLY",
)

if offline_mode():
    st.info("Offline field mode is active. Network-dependent source inspection remains unavailable; local evidence and readiness tools are still accessible.")

render_section_header(
    "Evidence pipeline",
    "Move from source ingestion to schema validation, calibration and field readiness without crowding the operator workspace.",
    "7 TOOLS",
)
row1_left, row1_mid, row1_right = st.columns(3, gap="large")
with row1_left:
    render_source_card("Operational data", "Load & validate", "Manage habitation, shelter and hazard datasets while preserving provenance and unknown values.")
    st.page_link("pages/9_Operational_Data.py", label="Open data workspace →", use_container_width=True)
with row1_mid:
    render_source_card("GIS evidence", "Inspect sources", "Review source metadata, layer coverage, CRS, legend and calibration readiness.")
    st.page_link("pages/10_GIS_Source_Inspector.py", label="Open GIS inspector →", use_container_width=True)
with row1_right:
    render_source_card("Schema mapping", "Validate contracts", "Map incoming columns to required analytical fields without fabricating missing operational values.")
    st.page_link("pages/12_Schema_Mapper.py", label="Open schema mapper →", use_container_width=True)

row2_left, row2_mid, row2_right = st.columns(3, gap="large")
with row2_left:
    render_source_card("Hazard calibration", "Source-specific only", "Review calibrated hazard-source contracts. Uncalibrated live context never changes baseline risk.")
    st.page_link("pages/11_Calibrated_Hazard_Source.py", label="Open calibration →", use_container_width=True)
with row2_mid:
    render_source_card("System readiness", "Field preflight", "Check offline assets, environment state and release-readiness diagnostics.")
    st.page_link("pages/8_System_Readiness.py", label="Open readiness →", use_container_width=True)
with row2_right:
    render_source_card("Methodology", "Explainable model", "Inspect the frozen risk equation, thresholds, assumptions and decision-support boundaries.")
    st.page_link("pages/6_Methodology.py", label="Open methodology →", use_container_width=True)

render_section_header(
    "Controlled scenario testing",
    "Keep what-if analysis clearly separated from live operational truth.",
    "SANDBOX",
)
scenario_left, boundary_right = st.columns([1.6, 1], gap="large")
with scenario_left:
    render_source_card(
        "Scenario Studio",
        "What-if analysis",
        "Explore controlled analytical scenarios without presenting hypothetical values as live operational truth.",
    )
    st.page_link("pages/5_Scenario_Studio.py", label="Open Scenario Studio →", use_container_width=True)
with boundary_right:
    render_decision_gate(
        "Analytical isolation",
        "Uncalibrated live context never changes baseline risk.",
        "ok",
    )
    render_decision_gate(
        "Unknown stays unknown",
        "Missing operational values are never silently fabricated or replaced with zero.",
        "ok",
    )
    st.page_link("pages/15_About_System.py", label="Review system boundaries →", use_container_width=True)

render_disclaimer()
