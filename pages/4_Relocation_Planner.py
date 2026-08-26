import streamlit as st
from src.ui_theme import render_data_mode_indicator, render_disclaimer

st.title("Relocation Planner")
render_data_mode_indicator("DEMO")
st.write("Workflow: select affected habitation → compare safe shelters → inspect capacity and route → export draft action plan.")
render_disclaimer()
