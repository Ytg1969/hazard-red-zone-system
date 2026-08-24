import streamlit as st
from src.ui_theme import render_data_mode_indicator, render_disclaimer

st.title("Red Zone Map")
render_data_mode_indicator("DEMO")
st.write("Interactive hazard and habitation map will be rendered here using the shared GIS outputs.")
render_disclaimer()
