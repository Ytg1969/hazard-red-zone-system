import pandas as pd
import plotly.express as px
import streamlit as st

from src.live_alerts import fetch_disaster_alerts
from src.pipeline import (
    calculate_summary,
    enrich_habitations,
    enrich_shelters,
    load_demo_data,
    load_demo_hazards,
)
from src.ui_theme import (
    inject_global_css,
    render_data_mode_indicator,
    render_disclaimer,
    render_kpi_strip,
    render_page_header,
)

st.set_page_config(page_title="Command Center", layout="wide")
inject_global_css()
render_page_header(
    "Command Center",
    "Operational summary of habitation risk, exposed population and shelter capacity.",
)
render_data_mode_indicator("DEMO")

try:
    habitations_raw, shelters_raw = load_demo_data()
    try:
        hazards = load_demo_hazards()
    except Exception:
        hazards = None
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards)
    shelters = enrich_shelters(shelters_raw)
except Exception:
    st.error("Unable to prepare the demonstration command-center dataset.")
    render_disclaimer()
    st.stop()

with st.sidebar:
    st.subheader("Filters")
    district_options = ["All"] + sorted(
        habitations["district_code"].dropna().astype(str).unique().tolist()
    )
    district = st.selectbox("District", district_options)
    risk_options = ["All", "CRITICAL", "HIGH", "MODERATE", "LOW"]
    risk_filter = st.selectbox("Risk level", risk_options)

filtered = habitations.copy()
if district != "All":
    filtered = filtered[filtered["district_code"].astype(str) == district]
if risk_filter != "All":
    filtered = filtered[filtered["risk_level"] == risk_filter]

summary = calculate_summary(filtered, shelters)
render_kpi_strip(
    [
        ("Habitations", f"{summary['habitations_monitored']:,}", None),
        ("Critical", f"{summary['critical_red_zones']:,}", None),
        ("Population at Risk", f"{summary['population_at_risk']:,}", None),
        ("Immediate Relocation", f"{summary['immediate_relocation_population']:,}", None),
        (
            "Shelter Capacity",
            f"{int(summary['available_shelter_capacity']):,}",
            "Available across all demo shelters",
        ),
    ]
)

st.divider()
tab1, tab2, tab3, tab4 = st.tabs(
    ["Risk Overview", "Habitation Data", "Shelter Capacity", "External Alerts"]
)

with tab1:
    left, right = st.columns(2, gap="large")
    with left:
        counts = (
            filtered["risk_level"]
            .value_counts()
            .reindex(["CRITICAL", "HIGH", "MODERATE", "LOW"], fill_value=0)
            .rename_axis("Risk Level")
            .reset_index(name="Habitations")
        )
        fig = px.bar(counts, x="Risk Level", y="Habitations", title="Habitations by Risk Class")
        fig.update_layout(margin=dict(l=20, r=20, t=55, b=20), height=360)
        st.plotly_chart(fig, width="stretch")

    with right:
        priority = (
            filtered["relocation_priority"]
            .value_counts()
            .reindex(["IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM", "MONITOR"], fill_value=0)
            .rename_axis("Priority")
            .reset_index(name="Habitations")
        )
        fig = px.bar(priority, x="Priority", y="Habitations", title="Relocation Priority")
        fig.update_layout(margin=dict(l=20, r=20, t=55, b=20), height=360)
        st.plotly_chart(fig, width="stretch")

    st.subheader("Highest-risk locations")
    table_columns = [
        "name",
        "population",
        "risk_score",
        "risk_level",
        "relocation_priority",
        "risk_drivers",
    ]
    if "hazard_type" in filtered.columns:
        table_columns.append("hazard_type")
    st.dataframe(
        filtered[table_columns].sort_values("risk_score", ascending=False),
        width="stretch",
        hide_index=True,
    )

with tab2:
    st.dataframe(
        filtered.sort_values("risk_score", ascending=False),
        width="stretch",
        hide_index=True,
    )

with tab3:
    total_available = shelters["available_capacity"].sum()
    total_effective = shelters["effective_capacity"].sum()
    total_occupied = shelters["current_occupancy"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Effective Capacity", f"{int(total_effective):,}")
    c2.metric("Current Occupancy", f"{int(total_occupied):,}")
    c3.metric("Available Capacity", f"{int(total_available):,}")
    st.dataframe(
        shelters[
            [
                "name",
                "effective_capacity",
                "current_occupancy",
                "available_capacity",
                "capacity_validation_status",
                "safety_score",
            ]
        ].sort_values("available_capacity", ascending=False),
        width="stretch",
        hide_index=True,
    )

with tab4:
    st.subheader("Optional CAP / RSS warning feed")
    st.caption(
        "The alert connector is isolated from the analytical pipeline. It is labelled LIVE only when "
        "a verified feed URL is configured; otherwise this panel uses DEMO fallback content."
    )
    alert_result = fetch_disaster_alerts()
    render_data_mode_indicator(alert_result["mode"])
    st.caption(f"Source: {alert_result['source']} | Retrieved: {alert_result['fetched_at']}")
    if alert_result.get("stale"):
        st.warning("The displayed alert feed is cached because the configured source could not be refreshed.")
    if alert_result.get("error"):
        st.warning("Configured alert source was unavailable; demonstration alerts are shown instead.")

    alerts = pd.DataFrame(alert_result.get("alerts", []))
    if alerts.empty:
        st.info("No alerts were returned by the configured feed.")
    else:
        display_columns = [
            column
            for column in ["event", "severity", "urgency", "area", "headline", "published"]
            if column in alerts.columns
        ]
        st.dataframe(alerts[display_columns], width="stretch", hide_index=True)

    st.info(
        "To enable a verified feed later, set SIH_SACHET_FEED_URL to the confirmed public CAP/RSS "
        "endpoint. Do not label an unverified URL as a live government source."
    )

render_disclaimer()
