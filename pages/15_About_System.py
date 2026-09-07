from __future__ import annotations

import streamlit as st

from src.ui_theme import inject_global_css, render_disclaimer, render_page_header

st.set_page_config(page_title="System Boundaries", page_icon="IN", layout="wide", initial_sidebar_state="auto")
inject_global_css()
render_page_header(
    "System Boundaries",
    "What Hazard Command does, what it does not do, and the analytical contracts that must remain true during UI changes.",
)

st.markdown("## Core analytical contract")
st.code("Risk = 0.35H + 0.25E + 0.25V + 0.15A")
st.markdown(
    "- **LOW:** 0–29\n"
    "- **MODERATE:** 30–49\n"
    "- **HIGH:** 50–69\n"
    "- **CRITICAL:** 70–100"
)

left, right = st.columns(2, gap="large")
with left:
    st.markdown("### The system can")
    st.markdown(
        "- Prioritize habitations using explainable deterministic risk.\n"
        "- Show source-labelled live/cached/demo context.\n"
        "- Rank relocation candidates behind safety and capacity gates.\n"
        "- Show route provenance and offline fallbacks.\n"
        "- Export reviewable administrative evidence."
    )
with right:
    st.markdown("### The system cannot")
    st.markdown(
        "- Issue an evacuation or relocation order.\n"
        "- Treat unavailable live feeds as an all-clear.\n"
        "- Change analytical risk from uncalibrated external observations.\n"
        "- Overbook shelter capacity.\n"
        "- Invent missing operational values."
    )

st.markdown("## UI redesign rule")
st.info("The interface may change completely. These analytical and safety boundaries may not change without a separately reviewed model/data decision.")

render_disclaimer()
