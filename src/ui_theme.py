import html

import streamlit as st


RISK_COLORS = {
    "LOW": "#34a853",
    "MODERATE": "#f9ab00",
    "HIGH": "#ea8600",
    "CRITICAL": "#dc3545",
}

MODE_COLORS = {
    "LIVE": ("#0f9d58", "rgba(15,157,88,.12)"),
    "CACHED": ("#f9ab00", "rgba(249,171,0,.12)"),
    "DEMO": ("#8ab4f8", "rgba(138,180,248,.10)"),
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
        :root {
            --eoc-bg:#0f1419;
            --eoc-surface:#171d26;
            --eoc-elevated:#202733;
            --eoc-border:#2d3745;
            --eoc-text:#e8eaed;
            --eoc-muted:#98a2b3;
            --eoc-accent:#4a9eff;
        }
        .block-container { max-width: 1500px; padding-top: 1.2rem; padding-bottom: 2.5rem; }
        h1, h2, h3 { letter-spacing: -0.025em; }
        h2 { margin-top: 1.2rem; }
        [data-testid="stSidebar"] { border-right:1px solid rgba(128,128,128,.16); }
        [data-testid="stMetric"] {
            background:linear-gradient(145deg,rgba(255,255,255,.035),rgba(255,255,255,.012));
            border:1px solid rgba(255,255,255,.09);
            border-radius:12px;
            padding:.9rem 1rem;
            box-shadow:0 8px 24px rgba(0,0,0,.08);
        }
        [data-testid="stMetricValue"] { font-weight:700; letter-spacing:-.02em; }
        [data-testid="stDataFrame"] { border:1px solid rgba(128,128,128,.16); border-radius:10px; overflow:hidden; }
        .stTabs [data-baseweb="tab-list"] { gap:.35rem; border-bottom:1px solid rgba(128,128,128,.18); }
        .stTabs [data-baseweb="tab"] { border-radius:8px 8px 0 0; padding:.55rem .8rem; }
        .stButton > button, .stDownloadButton > button { border-radius:8px; font-weight:650; min-height:2.55rem; }
        .eoc-page-header {
            position:relative;
            background:linear-gradient(120deg,rgba(74,158,255,.10),rgba(74,158,255,.015) 55%,transparent);
            border:1px solid rgba(74,158,255,.14);
            border-radius:12px;
            padding:1rem 1.15rem;
            margin-bottom:1rem;
            overflow:hidden;
        }
        .eoc-page-header:before {
            content:"";
            position:absolute;
            left:0; top:0; bottom:0; width:4px;
            background:#4a9eff;
        }
        .eoc-page-header h1 { margin:0; font-size:1.7rem; }
        .eoc-page-header p { margin:.35rem 0 0; color:#98a2b3; max-width:1050px; }
        .eoc-mode {
            display:inline-flex;
            align-items:center;
            gap:.35rem;
            border-radius:999px;
            padding:.28rem .62rem;
            font-size:.72rem;
            font-weight:750;
            letter-spacing:.045em;
        }
        .eoc-mode-dot { width:.48rem; height:.48rem; border-radius:999px; display:inline-block; }
        .eoc-risk-badge { display:inline-block; color:white; border-radius:999px; padding:.24rem .62rem; font-size:.76rem; font-weight:750; letter-spacing:.02em; }
        .eoc-panel {
            border:1px solid rgba(128,128,128,.22);
            border-radius:12px;
            padding:1rem;
            margin-bottom:.75rem;
            background:rgba(255,255,255,.018);
        }
        .eoc-source-card {
            border:1px solid rgba(128,128,128,.20);
            border-radius:12px;
            padding:.9rem 1rem;
            background:linear-gradient(145deg,rgba(255,255,255,.028),rgba(255,255,255,.01));
            min-height:118px;
        }
        .eoc-source-card .title { font-size:.84rem; color:#98a2b3; margin-bottom:.25rem; }
        .eoc-source-card .value { font-size:1.12rem; font-weight:720; margin-bottom:.3rem; }
        .eoc-source-card .detail { font-size:.78rem; color:#98a2b3; line-height:1.35; }
        .eoc-disclaimer { color:#98a2b3; font-size:.76rem; border-top:1px solid rgba(128,128,128,.2); margin-top:1.6rem; padding-top:.8rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, description: str) -> None:
    st.markdown(
        f"<div class='eoc-page-header'><h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></div>",
        unsafe_allow_html=True,
    )


def render_data_mode_indicator(mode: str = "DEMO") -> None:
    mode = str(mode).upper()
    label = {"LIVE": "LIVE DATA", "CACHED": "CACHED DATA", "DEMO": "DEMONSTRATION DATA"}.get(mode, mode)
    foreground, background = MODE_COLORS.get(mode, ("#98a2b3", "rgba(152,162,179,.10)"))
    st.markdown(
        f"<span class='eoc-mode' style='color:{foreground};background:{background};border:1px solid {foreground}55'>"
        f"<span class='eoc-mode-dot' style='background:{foreground}'></span>{html.escape(label)}</span>",
        unsafe_allow_html=True,
    )


def render_source_card(title: str, value: str, detail: str) -> None:
    st.markdown(
        "<div class='eoc-source-card'>"
        f"<div class='title'>{html.escape(str(title))}</div>"
        f"<div class='value'>{html.escape(str(value))}</div>"
        f"<div class='detail'>{html.escape(str(detail))}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


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
        f"<span class='eoc-risk-badge' style='background:{color}'>{html.escape(level)}</span>",
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
