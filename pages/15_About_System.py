from __future__ import annotations

import streamlit as st

from src.ui_theme import (
    inject_global_css,
    render_context_bar,
    render_decision_gate,
    render_disclaimer,
    render_page_header,
    render_section_header,
    render_source_card,
)

st.set_page_config(page_title="System Boundaries", page_icon="IN", layout="wide", initial_sidebar_state="collapsed")
inject_global_css()
render_page_header(
    "System Boundaries",
    "The non-negotiable analytical and operational contracts behind Hazard Command, independent of how the interface changes.",
)
render_context_bar("Safety contract", "Model · provenance · capacity · authority", "NON-NEGOTIABLE")

render_section_header(
    "Analytical contract",
    "The UI can change radically; the approved model and classification thresholds do not change with it.",
    "FROZEN MODEL",
)
model_left, model_right = st.columns([1.25, 1], gap="large")
with model_left:
    render_source_card(
        "Risk equation",
        "0.35H + 0.25E + 0.25V + 0.15A",
        "Hazard, exposure, vulnerability and evacuation/accessibility contributions remain transparent and deterministic.",
    )
    st.code("Risk = 0.35H + 0.25E + 0.25V + 0.15A")
with model_right:
    render_decision_gate("LOW", "0–29 analytical risk", "ok")
    render_decision_gate("MODERATE", "30–49 analytical risk", "warn")
    render_decision_gate("HIGH", "50–69 analytical risk", "warn")
    render_decision_gate("CRITICAL", "70–100 analytical risk", "danger")

render_section_header(
    "Operational guardrails",
    "These constraints remain true across Command, Map, Risk, Relocation and Briefing.",
    "SAFETY",
)
can_col, cannot_col = st.columns(2, gap="large")
with can_col:
    st.markdown("### The system can")
    render_decision_gate("Prioritize", "Rank habitations using explainable deterministic risk.", "ok")
    render_decision_gate("Corroborate", "Show source-labelled LIVE/CACHED/DEMO context.", "ok")
    render_decision_gate("Constrain", "Rank relocation candidates only after safety and available-capacity gates.", "ok")
    render_decision_gate("Explain routes", "Show routing provenance, cache state and explicit fallbacks.", "ok")
    render_decision_gate("Export", "Generate reviewable administrative evidence and draft plans.", "ok")
with cannot_col:
    st.markdown("### The system cannot")
    render_decision_gate("Issue orders", "It cannot issue an evacuation or relocation order.", "danger")
    render_decision_gate("Assume all-clear", "Unavailable live feeds cannot be interpreted as no hazard.", "danger")
    render_decision_gate("Mutate risk silently", "Uncalibrated external observations cannot change baseline analytical risk.", "danger")
    render_decision_gate("Overbook shelters", "Shared shelter capacity cannot be allocated more than once.", "danger")
    render_decision_gate("Invent data", "Missing operational values remain unknown until verified.", "danger")

render_section_header(
    "Interface rule",
    "Presentation can be replaced completely without weakening the contracts above.",
    "UI ≠ MODEL",
)
st.info("The interface may change completely. These analytical and safety boundaries may not change without a separately reviewed model/data decision.")
st.page_link("pages/14_Evidence_Center.py", label="Return to Evidence Center →", use_container_width=True)

render_disclaimer()
