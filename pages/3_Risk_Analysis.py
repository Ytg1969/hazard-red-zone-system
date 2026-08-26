import streamlit as st
from src.ui_theme import render_data_mode_indicator, render_disclaimer

st.title("Risk Analysis")
render_data_mode_indicator("DEMO")
st.write("Select a habitation to view the 0–100 score, risk class and factor contributions.")
render_disclaimer()
