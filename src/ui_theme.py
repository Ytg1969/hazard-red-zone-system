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
            --eoc-bg:#08111c;
            --eoc-bg-soft:#0d1724;
            --eoc-surface:#101b29;
            --eoc-surface-2:#152235;
            --eoc-surface-3:#1a2a40;
            --eoc-border:rgba(145,166,192,.17);
            --eoc-border-strong:rgba(125,183,255,.35);
            --eoc-text:#eef5fb;
            --eoc-muted:#9dadbd;
            --eoc-accent:#68aefc;
            --eoc-accent-2:#4fd1c5;
            --eoc-warning:#f7b84b;
            --eoc-danger:#ff6678;
            --eoc-radius:18px;
            --eoc-shadow:0 22px 60px rgba(0,0,0,.24);
        }

        html { scroll-behavior:smooth; }
        body { font-feature-settings:"ss01" 1,"cv02" 1; }
        .stApp {
            background:
                radial-gradient(circle at 8% -6%, rgba(63,139,227,.14), transparent 27%),
                radial-gradient(circle at 94% 4%, rgba(79,209,197,.08), transparent 24%),
                linear-gradient(180deg,#08111c 0%,#0b1521 38%,#09121d 100%);
            color:var(--eoc-text);
        }
        [data-testid="stAppViewContainer"] > .main { background:transparent; }
        [data-testid="stHeader"] {
            background:rgba(8,17,28,.78);
            backdrop-filter:blur(14px);
            border-bottom:1px solid rgba(145,166,192,.09);
        }
        .block-container { max-width:1540px; padding-top:1.25rem; padding-bottom:3.2rem; }
        h1,h2,h3 { letter-spacing:-0.032em; }
        h1 { font-weight:760; }
        h2 { margin-top:1.3rem; font-size:1.35rem; }
        h3 { color:#f3f8fd; font-size:1.02rem; }
        p,li { line-height:1.58; }
        a { color:#86bdf8 !important; text-underline-offset:3px; }

        /* Navigation / application shell */
        [data-testid="stSidebar"] {
            border-right:1px solid var(--eoc-border);
            background:linear-gradient(180deg,rgba(10,19,30,.99),rgba(7,14,23,.99));
            box-shadow:18px 0 48px rgba(0,0,0,.14);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top:.45rem; }
        [data-testid="stSidebarNav"] {
            padding:.35rem .45rem .8rem;
            border-bottom:1px solid rgba(145,166,192,.10);
            margin-bottom:.55rem;
        }
        [data-testid="stSidebarNav"]:before {
            content:"EOC OPERATIONS";
            display:block;
            margin:.35rem .7rem .75rem;
            color:#7e94aa;
            font-size:.64rem;
            font-weight:800;
            letter-spacing:.16em;
        }
        [data-testid="stSidebarNav"] a {
            min-height:42px;
            display:flex;
            align-items:center;
            border-radius:11px;
            margin:.14rem .18rem;
            padding-left:.55rem;
            border:1px solid transparent;
            transition:background .18s ease,transform .18s ease,border-color .18s ease;
        }
        [data-testid="stSidebarNav"] a:hover {
            background:rgba(105,174,252,.08);
            border-color:rgba(105,174,252,.14);
            transform:translateX(2px);
        }
        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background:linear-gradient(90deg,rgba(105,174,252,.15),rgba(79,209,197,.04));
            border-color:rgba(105,174,252,.22);
            box-shadow:inset 3px 0 0 #69aefc;
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
            font-size:.72rem;
            text-transform:uppercase;
            letter-spacing:.12em;
            color:#8297aa;
            margin-top:1.1rem;
        }

        /* Website-like content surfaces */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius:var(--eoc-radius);
        }
        [data-testid="stMetric"] {
            position:relative;
            background:linear-gradient(145deg,rgba(255,255,255,.052),rgba(255,255,255,.015));
            border:1px solid var(--eoc-border);
            border-radius:15px;
            padding:1.02rem 1.08rem;
            box-shadow:0 10px 30px rgba(0,0,0,.13);
            overflow:hidden;
            transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
        }
        [data-testid="stMetric"]:hover {
            transform:translateY(-2px);
            border-color:var(--eoc-border-strong);
            box-shadow:0 18px 42px rgba(0,0,0,.19);
        }
        [data-testid="stMetric"]:before {
            content:"";
            position:absolute;
            left:0; top:0; bottom:0; width:2px;
            background:linear-gradient(180deg,var(--eoc-accent),var(--eoc-accent-2),transparent 92%);
        }
        [data-testid="stMetricValue"] { font-weight:760; letter-spacing:-.04em; }
        [data-testid="stMetricLabel"] { color:#9fb1c2; font-size:.78rem; }

        [data-testid="stDataFrame"] {
            border:1px solid var(--eoc-border);
            border-radius:15px;
            overflow:hidden;
            box-shadow:0 14px 36px rgba(0,0,0,.11);
            background:rgba(255,255,255,.012);
        }
        [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {
            border:1px solid var(--eoc-border);
            border-radius:15px;
            padding:.45rem;
            background:linear-gradient(145deg,rgba(255,255,255,.026),rgba(255,255,255,.008));
            box-shadow:0 12px 32px rgba(0,0,0,.08);
        }
        iframe[title="streamlit_folium.st_folium"] {
            border:1px solid var(--eoc-border) !important;
            border-radius:17px !important;
            box-shadow:0 18px 46px rgba(0,0,0,.16) !important;
            overflow:hidden;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap:.42rem;
            border-bottom:1px solid var(--eoc-border);
            padding-bottom:.1rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius:10px 10px 0 0;
            padding:.62rem .9rem;
            transition:background .18s ease,color .18s ease;
        }
        .stTabs [aria-selected="true"] {
            background:rgba(105,174,252,.09);
            box-shadow:inset 0 -2px 0 #69aefc;
        }

        .stButton > button, .stDownloadButton > button {
            border-radius:11px;
            font-weight:700;
            min-height:2.68rem;
            border:1px solid rgba(125,183,255,.27);
            background:linear-gradient(180deg,rgba(105,174,252,.15),rgba(105,174,252,.055));
            box-shadow:0 8px 20px rgba(0,0,0,.11);
            transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease,background .16s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform:translateY(-1px);
            border-color:rgba(125,183,255,.52);
            background:linear-gradient(180deg,rgba(105,174,252,.20),rgba(105,174,252,.075));
            box-shadow:0 13px 28px rgba(0,0,0,.18);
        }
        .stButton > button:active, .stDownloadButton > button:active { transform:translateY(0); }

        [data-baseweb="select"] > div,
        [data-testid="stFileUploaderDropzone"],
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea {
            border-radius:11px !important;
            border-color:rgba(145,166,192,.22) !important;
            background:rgba(255,255,255,.025) !important;
            transition:border-color .16s ease,box-shadow .16s ease;
        }
        [data-baseweb="select"] > div:focus-within,
        [data-testid="stTextInput"] input:focus,
        [data-testid="stNumberInput"] input:focus,
        [data-testid="stTextArea"] textarea:focus {
            border-color:rgba(105,174,252,.58) !important;
            box-shadow:0 0 0 3px rgba(105,174,252,.08) !important;
        }
        [data-testid="stExpander"] {
            border:1px solid var(--eoc-border);
            border-radius:13px;
            background:linear-gradient(145deg,rgba(255,255,255,.024),rgba(255,255,255,.008));
            overflow:hidden;
        }
        [data-testid="stAlert"] {
            border-radius:13px;
            border-width:1px;
            box-shadow:0 9px 26px rgba(0,0,0,.08);
        }

        /* Product masthead */
        .eoc-page-header {
            position:relative;
            background:
                linear-gradient(116deg,rgba(55,122,204,.22),rgba(30,54,81,.09) 50%,rgba(79,209,197,.045)),
                rgba(255,255,255,.014);
            border:1px solid rgba(125,183,255,.21);
            border-radius:20px;
            padding:1.15rem 1.35rem 1.22rem;
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
        .eoc-topline {
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:1rem;
            margin-bottom:.65rem;
            position:relative;
            z-index:1;
        }
        .eoc-brand {
            display:flex;
            align-items:center;
            gap:.55rem;
            color:#b9c8d8;
            font-size:.69rem;
            font-weight:800;
            letter-spacing:.11em;
            text-transform:uppercase;
        }
        .eoc-brand-mark {
            width:24px;height:24px;border-radius:8px;
            display:grid;place-items:center;
            color:#07111b;font-size:.68rem;font-weight:900;
            background:linear-gradient(135deg,#75b5ff,#52d4c7);
            box-shadow:0 5px 16px rgba(82,166,255,.24);
        }
        .eoc-product-meta {
            display:flex;gap:.38rem;flex-wrap:wrap;justify-content:flex-end;
        }
        .eoc-chip {
            border:1px solid rgba(145,166,192,.18);
            border-radius:999px;
            padding:.23rem .52rem;
            color:#8fa5bb;
            font-size:.61rem;
            font-weight:730;
            letter-spacing:.045em;
            background:rgba(4,10,17,.24);
        }
        .eoc-eyebrow {
            display:flex;align-items:center;gap:.5rem;margin-bottom:.42rem;
            color:#83a9cf;font-size:.66rem;font-weight:760;letter-spacing:.13em;text-transform:uppercase;
        }
        .eoc-eyebrow:before { content:"";width:22px;height:1px;background:linear-gradient(90deg,#69aefc,#4fd1c5); }
        .eoc-page-header h1 { margin:0; font-size:clamp(1.65rem,2.1vw,2.15rem); position:relative; z-index:1; }
        .eoc-page-header p { margin:.45rem 0 0; color:#a3b3c4; max-width:1120px; font-size:.94rem; position:relative; z-index:1; }

        .eoc-mode {
            display:inline-flex;align-items:center;gap:.4rem;border-radius:999px;padding:.30rem .68rem;
            font-size:.69rem;font-weight:800;letter-spacing:.055em;backdrop-filter:blur(8px);
        }
        .eoc-mode-dot { width:.48rem;height:.48rem;border-radius:999px;display:inline-block;box-shadow:0 0 0 3px rgba(255,255,255,.025); }
        .eoc-mode[data-mode="LIVE"] .eoc-mode-dot { animation:eocPulse 1.8s ease-out infinite; }
        @keyframes eocPulse { 0%{box-shadow:0 0 0 0 rgba(53,208,127,.45)} 70%{box-shadow:0 0 0 7px rgba(53,208,127,0)} 100%{box-shadow:0 0 0 0 rgba(53,208,127,0)} }

        .eoc-risk-badge {
            display:inline-flex;align-items:center;color:white;border-radius:999px;padding:.27rem .68rem;
            font-size:.74rem;font-weight:800;letter-spacing:.035em;
            box-shadow:inset 0 0 0 1px rgba(255,255,255,.18),0 6px 16px rgba(0,0,0,.16);
        }
        .eoc-panel {
            border:1px solid var(--eoc-border);border-radius:var(--eoc-radius);padding:1.05rem;margin-bottom:.8rem;
            background:linear-gradient(145deg,rgba(255,255,255,.029),rgba(255,255,255,.008));
            box-shadow:0 12px 32px rgba(0,0,0,.10);
        }
        .eoc-source-card {
            position:relative;border:1px solid var(--eoc-border);border-radius:16px;padding:1.05rem 1.08rem;
            background:linear-gradient(145deg,rgba(255,255,255,.035),rgba(255,255,255,.009));
            min-height:128px;overflow:hidden;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease;
        }
        .eoc-source-card:hover { transform:translateY(-2px);border-color:var(--eoc-border-strong);box-shadow:0 14px 34px rgba(0,0,0,.13); }
        .eoc-source-card:after {
            content:"";position:absolute;width:74px;height:74px;right:-28px;bottom:-31px;border-radius:50%;
            background:radial-gradient(circle,rgba(105,174,252,.13),transparent 68%);
        }
        .eoc-source-card .title { font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;color:#8fa2b6;margin-bottom:.36rem; }
        .eoc-source-card .value { font-size:1.17rem;font-weight:750;margin-bottom:.36rem; }
        .eoc-source-card .detail { font-size:.79rem;color:#9eafc0;line-height:1.43; }
        .eoc-disclaimer { color:#8799ac;font-size:.74rem;border-top:1px solid var(--eoc-border);margin-top:1.9rem;padding-top:.95rem; }

        hr { border-color:var(--eoc-border) !important; }
        code { border-radius:8px !important; }

        @media (prefers-reduced-motion:reduce) {
            *,*:before,*:after { animation:none !important;transition:none !important;scroll-behavior:auto !important; }
        }
        @media (max-width:900px) {
            .block-container { padding-left:1rem;padding-right:1rem; }
            .eoc-page-header { padding:1rem;border-radius:15px; }
            .eoc-page-header:after { opacity:.42; }
            .eoc-product-meta { display:none; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str, description: str) -> None:
    st.markdown(
        "<div class='eoc-page-header'>"
        "<div class='eoc-topline'>"
        "<div class='eoc-brand'><span class='eoc-brand-mark'>HZ</span><span>Hazard Red-Zone Command Platform</span></div>"
        "<div class='eoc-product-meta'><span class='eoc-chip'>SIH26191</span><span class='eoc-chip'>Decision Support</span><span class='eoc-chip'>Multi-Hazard</span></div>"
        "</div>"
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
