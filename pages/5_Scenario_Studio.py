import streamlit as st
from src.risk_engine import DEFAULT_WEIGHTS
from src.ui_theme import render_data_mode_indicator, render_disclaimer

st.title("Scenario Studio")
render_data_mode_indicator("DEMO")
st.write("Adjust risk-factor emphasis for scenario analysis. Production deployments should calibrate defaults with domain experts.")

for name, value in DEFAULT_WEIGHTS.items():
    st.slider(name.title(), 0.0, 1.0, float(value), 0.05, disabled=True)

st.caption("Interactive reweighting will be enabled after the shared risk-data pipeline is merged.")
render_disclaimer()
