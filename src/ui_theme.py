import streamlit as st


RISK_COLORS = {
    "LOW": "#34a853",
    "MODERATE": "#f9ab00",
    "HIGH": "#ea8600",
    "CRITICAL": "#dc3545",
}

DEMO_CITY_OPTIONS = ["All Demo Cities", "Puri", "Guwahati", "Chennai"]
HAZARD_PROFILE_OPTIONS = {
    "Combined Multi-Hazard": "combined",
    "Flood": "flood",
    "Cyclone": "cyclone",
    "Landslide": "landslide",
    "Earthquake": "earthquake",
    "Drought": "drought",
    "Stored / GIS score": "stored",
}


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root { --eoc-bg:#0f1419; --eoc-surface:#171d26; --eoc-elevated:#202733; --eoc-border:#2d3745; --eoc-text:#e8eaed; --eoc-muted:#98a2b3; --eoc-accent:#4a9eff; }
        .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
        h1, h2, h3 { letter-spacing: -0.02em; }
        [data-testid="stMetric"] { background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:.85rem 1rem; }
        .eoc-page-header { border-bottom:1px solid rgba(128,128,128,.25); padding-bottom:.8rem; margin-bottom:1.1rem; }
        .eoc-page-header h1 { margin:0; font-size:1.65rem; }
        .eoc-page-header p { margin:.35rem 0 0; color:#98a2b3; }
        .eoc-mode { display:inline-block; border:1px solid rgba(128,128,128,.35); border-radius:999px; padding:.18rem .55rem; font-size:.75rem; font-weight:600; letter-spacing:.03em; }
        .eoc-risk-badge { display:inline-block; color:white; border-radius:999px; padding:.2rem .55rem; font-size:.78rem; font-weight:700; }
        .eoc-panel { border:1px solid rgba(128,128,128,.25); border-radius:8px; padding:1rem; margin-bottom:.75rem; }
        .eoc-disclaimer { color:#98a2b3; font-size:.78rem; border-top:1px solid rgba(128,128,128,.2); margin-top:1.5rem; padding-top:.75rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, description: str) -> None:
    st.markdown(
        f"<div class='eoc-page-header'><h1>{title}</h1><p>{description}</p></div>",
        unsafe_allow_html=True,
    )


def render_data_mode_indicator(mode: str = "DEMO") -> None:
    mode = mode.upper()
    label = {"LIVE": "LIVE DATA", "CACHED": "CACHED DATA", "DEMO": "DEMONSTRATION DATA"}.get(mode, mode)
    st.markdown(f"<span class='eoc-mode'>{label}</span>", unsafe_allow_html=True)


def render_demo_scope_controls(prefix: str = "demo") -> tuple[str, str]:
    """Render consistent multi-city/hazard controls and return (city, hazard_profile)."""
    with st.sidebar:
        st.subheader("Demo Scenario")
        city = st.selectbox("Geography", DEMO_CITY_OPTIONS, key=f"{prefix}_city")
        label = st.selectbox("Hazard profile", list(HAZARD_PROFILE_OPTIONS), key=f"{prefix}_hazard")
        st.caption(
            "Puri, Guwahati and Chennai use real geography with synthetic operational scenario values. "
            "Hazard-profile weights are transparent prototype assumptions, not official standards."
        )
    return city, HAZARD_PROFILE_OPTIONS[label]


def render_upload_controls(prefix: str = "upload"):
    """Optional custom CSV inputs. Uploaded records remain user-supplied, not LIVE government data."""
    with st.sidebar.expander("Custom CSV input", expanded=False):
        st.caption("Use the frozen required columns. Missing values are not fabricated.")
        habitations = st.file_uploader("Habitation CSV", type=["csv"], key=f"{prefix}_habitations")
        shelters = st.file_uploader("Shelter CSV", type=["csv"], key=f"{prefix}_shelters")
    return habitations, shelters


def render_risk_badge(level: str) -> None:
    level = str(level).upper()
    color = RISK_COLORS.get(level, "#6c757d")
    st.markdown(
        f"<span class='eoc-risk-badge' style='background:{color}'>{level}</span>",
        unsafe_allow_html=True,
    )


def render_kpi_strip(metrics: list[tuple[str, object, str | None]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value, help_text) in zip(columns, metrics):
        column.metric(label, value, help=help_text)


def render_empty_state(message: str) -> None:
    st.info(message)


def render_disclaimer() -> None:
    st.markdown(
        "<div class='eoc-disclaimer'>Decision-support prototype only. Final evacuation, relocation and emergency orders remain with authorized disaster-management officials. Multi-city operational values and hazard footprints bundled with the app are DEMO scenario data unless an authoritative source is explicitly identified.</div>",
        unsafe_allow_html=True,
    )
