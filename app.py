from pathlib import Path
import pandas as pd
import streamlit as st

from src.carrying_capacity import calculate_capacity
from src.risk_engine import calculate_risk
from src.vulnerability import calculate_vulnerability
from src.ui_theme import render_data_mode_indicator, render_disclaimer

st.set_page_config(page_title="Multi-Hazard Decision Support System", layout="wide")

st.title("Multi-Hazard Decision Support System")
st.caption("Emergency Operations Centre | SIH26191")
render_data_mode_indicator("DEMO")

hab_path = Path("data/demo/habitations.csv")
shelter_path = Path("data/demo/shelters.csv")

try:
    habitations = pd.read_csv(hab_path)
    shelters = pd.read_csv(shelter_path)

    risk_rows = []
    for record in habitations.to_dict("records"):
        vulnerability = calculate_vulnerability(record)
        record["vulnerability_score"] = vulnerability["vulnerability_score"]
        risk = calculate_risk(record)
        risk_rows.append({**record, **risk})

    risk_df = pd.DataFrame(risk_rows)

    available_capacity = 0.0
    for shelter in shelters.to_dict("records"):
        available_capacity += calculate_capacity(shelter)["available_capacity"]

    critical = int((risk_df["risk_level"] == "CRITICAL").sum())
    at_risk = int(risk_df.loc[risk_df["risk_level"].isin(["HIGH", "CRITICAL"]), "population"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Habitations Monitored", len(risk_df))
    c2.metric("Critical Red Zones", critical)
    c3.metric("Population at Risk", f"{at_risk:,}")
    c4.metric("Available Shelter Capacity", f"{int(available_capacity):,}")

    st.subheader("Current Demonstration Situation")
    show_cols = ["name", "population", "risk_score", "risk_level", "drivers"]
    st.dataframe(risk_df[show_cols].sort_values("risk_score", ascending=False), use_container_width=True, hide_index=True)

    st.subheader("Operational workflow")
    st.write("Data → GIS Exposure → Vulnerability → Risk → Carrying Capacity → Routing → Relocation → Action Plan")

except Exception as exc:
    st.error("The demonstration dataset could not be loaded or processed.")
    st.exception(exc)

render_disclaimer()
