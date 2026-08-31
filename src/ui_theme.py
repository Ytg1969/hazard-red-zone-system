import html

import streamlit as st


RISK_COLORS = {
    "LOW": "#34a853",
    "MODERATE": "#f9ab00",
    "HIGH": "#ea8600",
    "CRITICAL": "#dc3545",
}

MODE_COLORS = {
    "LIVE": ("#35d07f", "rgba(53,208,127,.12)"),
    "CACHED": ("#f7b84b", "rgba(247,184,75,.12)"),
    "DEMO": ("#7db7ff", "rgba(125,183,255,.11)"),
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
            --eoc-bg:#0a1018;
            --eoc-surface:#121a25;
            --eoc-surface-2:#182331;
            --eoc-border:rgba(145,166,192,.18);
            --eoc-border-strong:rgba(125,183,255,.28);
            --eoc-text:#edf4fb;
            --eoc-muted:#9aabbd;
            --eoc-accent:#69aefc;
            --eoc-accent-2:#4fd1c5;
            --eoc-warning:#f7b84b;
            --eoc-danger:#ff6678;
            --eoc-radius:16px;
            --eoc-shadow:0 18px 55px rgba(0,0,0,.24);
        }

        html { scroll-behavior:smooth; }
        .stApp {
            background:
                radial-gradient(circle at 10% -8%, rgba(61,135,220,.12), transparent 30%),
                radial-gradient(circle at 93% 6%, rgba(79,209,197,.07), transparent 25%),
                linear-gradient(180deg,#0a1018 0%,#0d141d 42%,#0b1119 100%);
            color:var(--eoc-text);
        }
        .block-container { max-width:1520px; padding-top:1.1rem; padding-bottom:3rem; }
        h1,h2,h3 { letter-spacing:-0.028em; }
        h2 { margin-top:1.3rem; }
        h3 { color:#f2f7fc; }
        p, li { line-height:1.55; }

        /* Sidebar feels like an operator console rather than a default form panel. */
        [data-testid="stSidebar"] {
            border-right:1px solid var(--eoc-border);
            background:linear-gradient(180deg,rgba(12,20,30,.985),rgba(9,15,23,.985));
            box-shadow:14px 0 38px rgba(0,0,0,.10);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
            font-size:.82rem;
            text-transform:uppercase;
            letter-spacing:.11em;
            color:#90a4b9;
            margin-top:1rem;
        }
        [data-testid="stSidebarNav"] a {
            border-radius:10px;
            margin:.12rem .28rem;
            transition:background .18s ease, transform .18s ease, color .18s ease;
        }
        [data-testid="stSidebarNav"] a:hover {
            background:rgba(105,174,252,.09);
            transform:translateX(2px);
        }

        /* Metrics are tactile but restrained; not every panel looks identical. */
        [data-testid="stMetric"] {
            position:relative;
            background:linear-gradient(145deg,rgba(255,255,255,.048),rgba(255,255,255,.016));
            border:1px solid var(--eoc-border);
            border-radius:14px;
            padding:1rem 1.05rem;
            box-shadow:0 10px 30px rgba(0,0,0,.12);
            overflow:hidden;
            transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
        }
        [data-testid="stMetric"]:hover {
            transform:translateY(-2px);
            border-color:var(--eoc-border-strong);
            box-shadow:0 16px 38px rgba(0,0,0,.18);
        }
        [data-testid="stMetric"]:before {
            content:"";
            position:absolute;
            left:0; top:0; bottom:0; width:2px;
            background:linear-gradient(180deg,var(--eoc-accent),transparent 82%);
            opacity:.85;
        }
        [data-testid="stMetricValue"] { font-weight:740; letter-spacing:-.035em; }
        [data-testid="stMetricLabel"] { color:#9eb0c2; }

        [data-testid="stDataFrame"] {
            border:1px solid var(--eoc-border);
            border-radius:14px;
            overflow:hidden;
            box-shadow:0 12px 34px rgba(0,0,0,.10);
        }
        [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {
            border:1px solid var(--eoc-border);
            border-radius:14px;
            padding:.35rem;
            background:rgba(255,255,255,.012);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap:.35rem;
            border-bottom:1px solid var(--eoc-border);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius:10px 10px 0 0;
            padding:.58rem .88rem;
            transition:background .18s ease,color .18s ease;
        }
        .stTabs [aria-selected="true"] { background:rgba(105,174,252,.09); }

        .stButton > button, .stDownloadButton > button {
            border-radius:10px;
            font-weight:680;
            min-height:2.6rem;
            border:1px solid rgba(125,183,255,.25);
            background:linear-gradient(180deg,rgba(105,174,252,.13),rgba(105,174,252,.055));
            box-shadow:0 7px 18px rgba(0,0,0,.10);
            transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform:translateY(-1px);
            border-color:rgba(125,183,255,.48);
            box-shadow:0 11px 24px rgba(0,0,0,.16);
        }
        .stButton > button:active, .stDownloadButton > button:active { transform:translateY(0); }

        [data-baseweb="select"] > div,
        [data-testid="stFileUploaderDropzone"],
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input {
            border-radius:10px !important;
            border-color:rgba(145,166,192,.20) !important;
        }
        [data-testid="stExpander"] {
            border:1px solid var(--eoc-border);
            border-radius:12px;
            background:rgba(255,255,255,.012);
        }

        .eoc-page-header {
            position:relative;
            background:
                linear-gradient(116deg,rgba(55,122,204,.20),rgba(30,54,81,.08) 50%,rgba(79,209,197,.035)),
                rgba(255,255,255,.012);
            border:1px solid rgba(125,183,255,.19);
            border-radius:18px;
            padding:1.25rem 1.35rem 1.18rem;
            margin-bottom:1rem;
            overflow:hidden;
            box-shadow:var(--eoc-shadow);
        }
        .eoc-page-header:before {
            content:"";
            position:absolute;
            left:0; top:0; bottom:0; width:4px;
            background:linear-gradient(180deg,#7db7ff,#4fd1c5);
        }
        .eoc-page-header:after {
            content:"";
            position:absolute;
            width:260px; height:260px;
            right:-118px; top:-152px;
            border:1px solid rgba(125,183,255,.12);
            border-radius:50%;
            box-shadow:0 0 0 42px rgba(125,183,255,.025),0 0 0 86px rgba(79,209,197,.018);
            pointer-events:none;
        }
        .eoc-eyebrow {
            display:flex;
            align-items:center;
            gap:.5rem;
            margin-bottom:.42rem;
            color:#83a9cf;
            font-size:.68rem;
            font-weight:760;
            letter-spacing:.13em;
            text-transform:uppercase;
        }
        .eoc-eyebrow:before {
            content:"";
            width:22px; height:1px;
            background:linear-gradient(90deg,#69aefc,#4fd1c5);
        }
        .eoc-page-header h1 { margin:0; font-size:clamp(1.55rem,2vw,2rem); }
        .eoc-page-header p { margin:.42rem 0 0; color:#a0b0c1; max-width:1100px; font-size:.94rem; }

        .eoc-mode {
            display:inline-flex;
            align-items:center;
            gap:.4rem;
            border-radius:999px;
            padding:.30rem .68rem;
            font-size:.70rem;
            font-weight:780;
            letter-spacing:.055em;
            backdrop-filter:blur(8px);
        }
        .eoc-mode-dot {
            width:.48rem; height:.48rem;
            border-radius:999px;
            display:inline-block;
            box-shadow:0 0 0 3px rgba(255,255,255,.025);
        }
        .eoc-mode[data-mode="LIVE"] .eoc-mode-dot { animation:eocPulse 1.8s ease-out infinite; }
        @keyframes eocPulse {
            0% { box-shadow:0 0 0 0 rgba(53,208,127,.45); }
            70% { box-shadow:0 0 0 7px rgba(53,208,127,0); }
            100% { box-shadow:0 0 0 0 rgba(53,208,127,0); }
        }

        .eoc-risk-badge {
            display:inline-flex;
            align-items:center;
            color:white;
            border-radius:999px;
            padding:.26rem .66rem;
            font-size:.74rem;
            font-weight:780;
            letter-spacing:.035em;
            box-shadow:inset 0 0 0 1px rgba(255,255,255,.18),0 6px 16px rgba(0,0,0,.16);
        }
        .eoc-panel {
            border:1px solid var(--eoc-border);
            border-radius:var(--eoc-radius);
            padding:1rem;
            margin-bottom:.8rem;
            background:linear-gradient(145deg,rgba(255,255,255,.026),rgba(255,255,255,.008));
            box-shadow:0 12px 32px rgba(0,0,0,.10);
        }
        .eoc-source-card {
            position:relative;
            border:1px solid var(--eoc-border);
            border-radius:15px;
            padding:1rem 1.05rem;
            background:linear-gradient(145deg,rgba(255,255,255,.032),rgba(255,255,255,.009));
            min-height:124px;
            overflow:hidden;
            transition:transform .18s ease,border-color .18s ease;
        }
        .eoc-source-card:hover { transform:translateY(-2px); border-color:var(--eoc-border-strong); }
        .eoc-source-card:after {
            content:"";
            position:absolute;
            width:70px; height:70px;
            right:-26px; bottom:-30px;
            border-radius:50%;
            background:radial-gradient(circle,rgba(105,174,252,.12),transparent 68%);
        }
        .eoc-source-card .title { font-size:.75rem; text-transform:uppercase; letter-spacing:.075em; color:#90a2b5; margin-bottom:.35rem; }
        .eoc-source-card .value { font-size:1.16rem; font-weight:735; margin-bottom:.35rem; }
        .eoc-source-card .detail { font-size:.79rem; color:#9eafc0; line-height:1.42; }
        .eoc-disclaimer { color:#8fa1b4; font-size:.75rem; border-top:1px solid var(--eoc-border); margin-top:1.8rem; padding-top:.9rem; }

        [data-testid="stAlert"] {
            border-radius:12px;
            border-width:1px;
            box-shadow:0 8px 24px rgba(0,0,0,.08);
        }
        hr { border-color:var(--eoc-border) !important; }

        /* Keep motion subtle and respectful of OS accessibility settings. */
        @media (prefers-reduced-motion: reduce) {
            *, *:before, *:after { animation:none !important; transition:none !important; scroll-behavior:auto !important; }
        }
        @media (max-width: 900px) {
            .block-container { padding-left:1rem; padding-right:1rem; }
            .eoc-page-header { padding:1rem 1rem 1rem 1.08rem; border-radius:14px; }
            .eoc-page-header:after { opacity:.55; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, description: str) -> None:
    st.markdown(
        "<div class='eoc-page-header'>"
        "<div class='eoc-eyebrow'>Emergency Operations Intelligence</div>"
        f"<h1>{html.escape(title)}</h1><p>{html.escape(description)}</p></div>",
        unsafe_allow_html=True,
    )


def render_data_mode_indicator(mode: str = "DEMO") -> None:
    mode = str(mode).upper()
    label = {"LIVE": "LIVE DATA", "CACHED": "CACHED DATA", "DEMO": "DEMONSTRATION DATA"}.get(mode, mode)
    foreground, background = MODE_COLORS.get(mode, ("#98a2b3", "rgba(152,162,179,.10)"))
    st.markdown(
        f"<span class='eoc-mode' data-mode='{html.escape(mode)}' style='color:{foreground};background:{background};border:1px solid {foreground}55'>"
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
