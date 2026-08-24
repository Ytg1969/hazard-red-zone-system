import streamlit as st


def render_data_mode_indicator(mode: str = "DEMO") -> None:
    mode = mode.upper()
    label = {"LIVE": "Live Data", "CACHED": "Cached Data", "DEMO": "Demonstration Data"}.get(mode, mode)
    st.caption(f"Data mode: {label}")


def render_disclaimer() -> None:
    st.caption("Decision-support prototype only. Final evacuation and relocation decisions remain with authorized disaster-management officials.")
