import streamlit as st
from src.ui_theme import render_data_mode_indicator, render_disclaimer

st.title("Command Center")
render_data_mode_indicator("DEMO")
st.write("Operational summary, filters, key risk metrics and shelter-capacity status will be integrated here.")
render_disclaimer()
