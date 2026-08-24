import streamlit as st

st.set_page_config(page_title="Multi-Hazard Decision Support System", layout="wide")

st.title("Multi-Hazard Decision Support System")
st.caption("Emergency Operations Centre | SIH26191")

st.info("DATA MODE: DEMO — live adapters are added separately and must never be implied when cached or demonstration data is in use.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Habitations Monitored", "—")
c2.metric("Critical Red Zones", "—")
c3.metric("Population at Risk", "—")
c4.metric("Available Shelter Capacity", "—")

st.subheader("Operational workflow")
st.write("Data → GIS Exposure → Vulnerability → Risk → Carrying Capacity → Routing → Relocation → Action Plan")

st.warning("Decision-support prototype only. Final evacuation and relocation decisions remain with authorized disaster-management officials.")
