import html

import streamlit as st


RISK_COLORS = {
    "LOW": "#26C281",
    "MODERATE": "#F7C948",
    "HIGH": "#FF9F43",
    "CRITICAL": "#FF5D73",
}

MODE_COLORS = {
    "LIVE": ("#42D392", "rgba(66,211,146,.12)"),
    "CACHED": ("#F7C948", "rgba(247,201,72,.12)"),
    "DEMO": ("#71B7FF", "rgba(113,183,255,.12)"),
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

CORE_NAV = [
    ("Overview", "app.py", "⌂"),
    ("Operations", "pages/0_Operations_Hub.py", "◎"),
    ("Red Zone Map", "pages/2_Red_Zone_Map.py", "◉"),
    ("Risk Analysis", "pages/3_Risk_Analysis.py", "◒"),
    ("Relocation", "pages/4_Relocation_Planner.py", "⇢"),
    ("Live Context", "pages/7_Live_Data_Context.py", "◌"),
    ("Operational Data", "pages/9_Operational_Data.py", "▦"),
]

TECH_NAV = [
    ("System Readiness", "pages/8_System_Readiness.py"),
    ("GIS Source Inspector", "pages/10_GIS_Source_Inspector.py"),
    ("Hazard Calibration", "pages/11_Calibrated_Hazard_Source.py"),
    ("Schema Mapper", "pages/12_Schema_Mapper.py"),
    ("Methodology", "pages/6_Methodology.py"),
    ("Scenario Studio", "pages/5_Scenario_Studio.py"),
    ("Command Center", "pages/1_Command_Center.py"),
]


def _render_navigation() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div class="hz-brand">
              <div class="hz-logo">HZ</div>
              <div><strong>Hazard Command</strong><span>SIH26191</span></div>
            </div>
            <div class="hz-nav-label">OPERATIONS</div>
            """,
            unsafe_allow_html=True,
        )
        for label, path, icon in CORE_NAV:
            st.page_link(path, label=f"{icon}  {label}", use_container_width=True)
        st.markdown('<div class="hz-nav-separator"></div>', unsafe_allow_html=True)
        with st.expander("Technical tools", expanded=False):
            for label, path in TECH_NAV:
                st.page_link(path, label=label, use_container_width=True)
        st.caption("Decision support · Source-aware · Capacity constrained")


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --hz-bg:#070B12;
          --hz-surface:#0D1420;
          --hz-surface-2:#111B29;
          --hz-surface-3:#162234;
          --hz-border:rgba(163,181,203,.14);
          --hz-border-strong:rgba(113,183,255,.38);
          --hz-text:#F4F7FB;
          --hz-muted:#93A4B8;
          --hz-accent:#5EA7FF;
          --hz-accent-2:#45D6C4;
          --hz-shadow:0 18px 55px rgba(0,0,0,.28);
        }
        html { scroll-behavior:smooth; }
        .stApp {
          background:
            radial-gradient(circle at 20% -10%, rgba(94,167,255,.13), transparent 34%),
            radial-gradient(circle at 90% 0%, rgba(69,214,196,.06), transparent 25%),
            var(--hz-bg);
          color:var(--hz-text);
        }
        [data-testid="stHeader"] {
          background:rgba(7,11,18,.72);
          border-bottom:1px solid rgba(255,255,255,.035);
          backdrop-filter:blur(16px);
        }
        .block-container { max-width:1480px; padding-top:1.15rem; padding-bottom:3.5rem; }
        h1,h2,h3 { letter-spacing:-.035em; }
        h1 { font-weight:800; }
        h2 { font-size:1.28rem; margin-top:1.4rem; }
        h3 { font-size:1rem; }
        p,li { line-height:1.58; }

        /* sidebar */
        [data-testid="stSidebar"] {
          background:linear-gradient(180deg,#0A1019 0%,#080D15 100%);
          border-right:1px solid var(--hz-border);
          box-shadow:16px 0 48px rgba(0,0,0,.18);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top:.55rem; }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
          border-radius:10px;
          min-height:40px;
          padding:.48rem .65rem;
          border:1px solid transparent;
          color:#C6D1DD !important;
          font-size:.89rem;
          font-weight:620;
          transition:all .16s ease;
        }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a:hover {
          color:white !important;
          background:rgba(94,167,255,.08);
          border-color:rgba(94,167,255,.16);
          transform:translateX(2px);
        }
        .hz-brand { display:flex; align-items:center; gap:.7rem; padding:.35rem .2rem 1rem; }
        .hz-logo { width:34px; height:34px; display:grid; place-items:center; border-radius:10px; font-size:.72rem; font-weight:900; color:#07101A; background:linear-gradient(135deg,#75B9FF,#45D6C4); box-shadow:0 8px 24px rgba(94,167,255,.25); }
        .hz-brand strong { display:block; color:#F3F7FB; font-size:.92rem; }
        .hz-brand span { display:block; color:#74879B; font-size:.64rem; letter-spacing:.1em; margin-top:.05rem; }
        .hz-nav-label { color:#60758A; font-size:.61rem; font-weight:800; letter-spacing:.15em; margin:.2rem .25rem .45rem; }
        .hz-nav-separator { height:1px; background:var(--hz-border); margin:.7rem 0; }
        [data-testid="stSidebar"] [data-testid="stExpander"] { border:none; background:transparent; }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary { color:#8294A8; font-size:.77rem; }

        /* primary content */
        .hz-hero {
          position:relative;
          overflow:hidden;
          border:1px solid rgba(113,183,255,.18);
          border-radius:22px;
          padding:1.35rem 1.45rem 1.42rem;
          background:linear-gradient(120deg,rgba(94,167,255,.14),rgba(255,255,255,.018) 48%,rgba(69,214,196,.045));
          box-shadow:var(--hz-shadow);
          margin-bottom:1rem;
        }
        .hz-hero:after { content:""; position:absolute; width:250px; height:250px; border-radius:50%; right:-110px; top:-145px; border:1px solid rgba(113,183,255,.12); box-shadow:0 0 0 38px rgba(94,167,255,.025),0 0 0 78px rgba(69,214,196,.015); }
        .hz-kicker { color:#7FA6CE; font-size:.64rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.48rem; }
        .hz-hero h1 { margin:0; font-size:clamp(1.72rem,2.4vw,2.42rem); max-width:1000px; position:relative; z-index:1; }
        .hz-hero p { margin:.48rem 0 0; color:#A8B7C7; max-width:1050px; font-size:.93rem; position:relative; z-index:1; }
        .hz-hero-meta { display:flex; gap:.4rem; flex-wrap:wrap; margin-top:.85rem; position:relative; z-index:1; }
        .hz-chip { border:1px solid rgba(163,181,203,.16); border-radius:999px; padding:.26rem .58rem; color:#91A4B9; font-size:.62rem; font-weight:700; background:rgba(4,8,13,.22); }

        [data-testid="stMetric"] {
          background:linear-gradient(145deg,rgba(255,255,255,.045),rgba(255,255,255,.012));
          border:1px solid var(--hz-border);
          border-radius:16px;
          padding:1rem 1.05rem;
          box-shadow:0 10px 28px rgba(0,0,0,.14);
        }
        [data-testid="stMetricValue"] { font-weight:800; letter-spacing:-.045em; }
        [data-testid="stMetricLabel"] { color:#91A3B5; font-size:.76rem; }
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {
          border:1px solid var(--hz-border);
          border-radius:16px;
          overflow:hidden;
          background:rgba(255,255,255,.012);
          box-shadow:0 12px 34px rgba(0,0,0,.10);
        }
        iframe[title="streamlit_folium.st_folium"] { border:1px solid var(--hz-border)!important; border-radius:18px!important; box-shadow:0 16px 42px rgba(0,0,0,.16)!important; overflow:hidden; }
        [data-testid="stAlert"] { border-radius:13px; border-width:1px; }
        [data-testid="stExpander"] { border:1px solid var(--hz-border); border-radius:13px; background:rgba(255,255,255,.015); overflow:hidden; }
        .stTabs [data-baseweb="tab-list"] { gap:.3rem; border-bottom:1px solid var(--hz-border); }
        .stTabs [data-baseweb="tab"] { border-radius:9px 9px 0 0; padding:.55rem .78rem; }
        .stTabs [aria-selected="true"] { background:rgba(94,167,255,.08); box-shadow:inset 0 -2px 0 var(--hz-accent); }
        .stButton > button, .stDownloadButton > button {
          border-radius:11px;
          min-height:2.6rem;
          font-weight:700;
          border:1px solid rgba(94,167,255,.28);
          background:linear-gradient(180deg,rgba(94,167,255,.16),rgba(94,167,255,.06));
          transition:all .16s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover { transform:translateY(-1px); border-color:rgba(94,167,255,.58); box-shadow:0 12px 28px rgba(0,0,0,.18); }
        [data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"], [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { border-radius:11px!important; border-color:rgba(163,181,203,.20)!important; background:rgba(255,255,255,.025)!important; }

        .hz-mode { display:inline-flex; align-items:center; gap:.42rem; border-radius:999px; padding:.3rem .68rem; font-size:.67rem; font-weight:800; letter-spacing:.05em; }
        .hz-dot { width:.45rem; height:.45rem; border-radius:50%; }
        .hz-risk { display:inline-flex; color:#fff; border-radius:999px; padding:.27rem .66rem; font-size:.72rem; font-weight:800; letter-spacing:.035em; box-shadow:inset 0 0 0 1px rgba(255,255,255,.18); }
        .hz-card { position:relative; min-height:120px; border:1px solid var(--hz-border); border-radius:16px; padding:1rem 1.05rem; background:linear-gradient(145deg,rgba(255,255,255,.034),rgba(255,255,255,.008)); }
        .hz-card .label { color:#8093A7; font-size:.66rem; font-weight:800; letter-spacing:.09em; text-transform:uppercase; }
        .hz-card .value { color:#F3F7FB; font-size:1.08rem; font-weight:760; margin:.36rem 0; }
        .hz-card .detail { color:#96A8BA; font-size:.79rem; line-height:1.45; }
        .hz-disclaimer { color:#77899C; font-size:.72rem; border-top:1px solid var(--hz-border); margin-top:2rem; padding-top:.95rem; }
        hr { border-color:var(--hz-border)!important; }

        @media (max-width:900px) {
          .block-container { padding-left:.9rem; padding-right:.9rem; }
          .hz-hero { border-radius:16px; padding:1.05rem; }
          .hz-hero:after { opacity:.35; }
        }
        @media (prefers-reduced-motion:reduce) { *,*:before,*:after { transition:none!important; animation:none!important; scroll-behavior:auto!important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
    _render_navigation()


def render_page_header(title: str, description: str) -> None:
    st.markdown(
        "<section class='hz-hero'>"
        "<div class='hz-kicker'>Hazard-based decision support</div>"
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(description)}</p>"
        "<div class='hz-hero-meta'><span class='hz-chip'>SIH26191</span><span class='hz-chip'>Explainable risk</span><span class='hz-chip'>Capacity-aware relocation</span></div>"
        "</section>",
        unsafe_allow_html=True,
    )


def render_data_mode_indicator(mode: str = "DEMO") -> None:
    mode = str(mode).upper()
    label = {"LIVE": "LIVE DATA", "CACHED": "CACHED DATA", "DEMO": "DEMONSTRATION DATA"}.get(mode, mode)
    foreground, background = MODE_COLORS.get(mode, ("#98A2B3", "rgba(152,162,179,.10)"))
    st.markdown(
        f"<span class='hz-mode' style='color:{foreground};background:{background};border:1px solid {foreground}55'><span class='hz-dot' style='background:{foreground}'></span>{html.escape(label)}</span>",
        unsafe_allow_html=True,
    )


def render_source_card(title: str, value: str, detail: str) -> None:
    st.markdown(
        "<div class='hz-card'>"
        f"<div class='label'>{html.escape(str(title))}</div>"
        f"<div class='value'>{html.escape(str(value))}</div>"
        f"<div class='detail'>{html.escape(str(detail))}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_demo_scope_controls(prefix: str = "demo") -> tuple[str, str]:
    with st.sidebar:
        st.markdown("### Scenario")
        city = st.selectbox("Geography", DEMO_CITY_OPTIONS, key=f"{prefix}_city")
        label = st.selectbox("Hazard profile", list(HAZARD_PROFILE_OPTIONS), key=f"{prefix}_hazard")
        st.caption("Demo geographies use synthetic operational scenario values unless an authoritative source is explicitly activated.")
    return city, HAZARD_PROFILE_OPTIONS[label]


def render_upload_controls(prefix: str = "upload"):
    with st.sidebar.expander("Custom CSV input", expanded=False):
        st.caption("Required fields are validated; missing values are not fabricated.")
        habitations = st.file_uploader("Habitation CSV", type=["csv"], key=f"{prefix}_habitations")
        shelters = st.file_uploader("Shelter CSV", type=["csv"], key=f"{prefix}_shelters")
    return habitations, shelters


def render_risk_badge(level: str) -> None:
    level = str(level).upper()
    color = RISK_COLORS.get(level, "#6C757D")
    st.markdown(f"<span class='hz-risk' style='background:{color}'>{html.escape(level)}</span>", unsafe_allow_html=True)


def render_kpi_strip(metrics: list[tuple[str, object, str | None]]) -> None:
    columns = st.columns(len(metrics))
    for column, (label, value, help_text) in zip(columns, metrics):
        column.metric(label, value, help=help_text)


def render_empty_state(message: str) -> None:
    st.info(message)


def render_disclaimer() -> None:
    st.markdown(
        "<div class='hz-disclaimer'>Decision-support system only. Evacuation, relocation and emergency orders remain with authorized disaster-management officials. Bundled operational values are demonstration data unless an authoritative source is explicitly identified.</div>",
        unsafe_allow_html=True,
    )
