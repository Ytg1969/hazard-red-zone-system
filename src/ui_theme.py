import html

import streamlit as st

from src.runtime_mode import offline_mode


RISK_COLORS = {
    "LOW": "#7BA05B",
    "MODERATE": "#D6A83B",
    "HIGH": "#C7771E",
    "CRITICAL": "#B64024",
}

MODE_COLORS = {
    "LIVE": ("#7BA05B", "rgba(123,160,91,.16)"),
    "CACHED": ("#D6A83B", "rgba(214,168,59,.17)"),
    "DEMO": ("#FFB000", "rgba(255,176,0,.13)"),
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
    ("Command", "app.py", "CMD"),
    ("Hazard Map", "pages/2_Red_Zone_Map.py", "MAP"),
    ("Risk", "pages/3_Risk_Analysis.py", "RISK"),
    ("Relocate", "pages/4_Relocation_Planner.py", "MOVE"),
    ("Briefing", "pages/13_Briefing.py", "BRF"),
]

MOBILE_NAV = [
    ("Command", "app.py", "⌂"),
    ("Map", "pages/2_Red_Zone_Map.py", "◉"),
    ("Relocate", "pages/4_Relocation_Planner.py", "⇢"),
    ("Brief", "pages/13_Briefing.py", "▤"),
]

SECONDARY_NAV = [
    ("Evidence Center", "pages/14_Evidence_Center.py"),
    ("System Boundaries", "pages/15_About_System.py"),
]

DATA_TOOL_NAV = [
    ("Operational Data", "pages/9_Operational_Data.py"),
    ("Scenario Studio", "pages/5_Scenario_Studio.py"),
    ("Live Context", "pages/7_Live_Data_Context.py"),
    ("System Readiness", "pages/8_System_Readiness.py"),
    ("GIS Source Inspector", "pages/10_GIS_Source_Inspector.py"),
    ("Hazard Calibration", "pages/11_Calibrated_Hazard_Source.py"),
    ("Schema Mapper", "pages/12_Schema_Mapper.py"),
    ("Methodology", "pages/6_Methodology.py"),
]


def _render_navigation() -> None:
    """Render a retro dispatch switchboard and a secondary control drawer."""
    with st.container(key="hz_topbar"):
        brand, ticker, nav1, nav2, nav3, nav4, nav5 = st.columns([1.15, 2.65, .86, .9, .82, .86, .82], gap="small")
        with brand:
            st.markdown(
                "<div class='hz-brand-block'><span class='hz-logo'>HZ</span>"
                "<span><strong>HAZARD COMMAND</strong><small>CIVIL DEFENCE BOARD</small></span></div>",
                unsafe_allow_html=True,
            )
        with ticker:
            st.markdown(
                "<div class='hz-top-ticker'><span>CYCLONE + FLOOD WATCH · ROUTE CACHE READY · CAPACITY GATED · DECISION SUPPORT ONLY · </span></div>",
                unsafe_allow_html=True,
            )
        for column, (label, path, icon) in zip([nav1, nav2, nav3, nav4, nav5], CORE_NAV):
            with column:
                st.page_link(path, label=f"{icon} {label}", use_container_width=True)

    with st.sidebar:
        st.markdown(
            "<div class='hz-drawer-brand'><span class='hz-logo'>HZ</span>"
            "<span><strong>CONTROL DRAWER</strong><small>Scope · sources · controls</small></span></div>",
            unsafe_allow_html=True,
        )
        if offline_mode():
            st.markdown(
                "<div class='hz-runtime hz-runtime-offline'><span></span>OFFLINE FIELD MODE</div>"
                "<div class='hz-runtime-note'>Network context is disabled. Local planning remains available.</div>",
                unsafe_allow_html=True,
            )
        with st.expander("Evidence & boundaries", expanded=False):
            for label, path in SECONDARY_NAV:
                st.page_link(path, label=label, use_container_width=True)
        with st.expander("Data & configuration", expanded=False):
            for label, path in DATA_TOOL_NAV:
                st.page_link(path, label=label, use_container_width=True)
        st.caption("dispatch board · source aware · capacity constrained")


def _render_mobile_navigation() -> None:
    with st.container(key="hz_mobile_nav"):
        columns = st.columns(len(MOBILE_NAV), gap="small")
        for column, (label, path, icon) in zip(columns, MOBILE_NAV):
            with column:
                st.page_link(path, label=f"{icon}\n{label}", use_container_width=True)


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --hz-bg:#17110A;
          --hz-bg-deep:#0E0905;
          --hz-cabinet:#2B1A0D;
          --hz-panel:#1B1209;
          --hz-panel-2:#24170B;
          --hz-paper:#E8D2A0;
          --hz-paper-dim:#C9A86A;
          --hz-amber:#FFB000;
          --hz-brass:#C59445;
          --hz-brass-dim:#7B5727;
          --hz-olive:#7BA05B;
          --hz-map:#1C2A18;
          --hz-red:#B64024;
          --hz-text:#FFE6A5;
          --hz-muted:#B88A45;
          --hz-line:rgba(197,148,69,.46);
        }
        @keyframes hz-ticker { from { transform:translateX(0); } to { transform:translateX(-42%); } }
        @keyframes hz-scan { 0%,100% { opacity:.18; } 50% { opacity:.36; } }
        @keyframes hz-blink { 0%,48% { opacity:1; } 49%,100% { opacity:.32; } }
        @keyframes hz-pulse { 0% { box-shadow:0 0 0 rgba(255,176,0,0); } 50% { box-shadow:0 0 24px rgba(255,176,0,.22); } 100% { box-shadow:0 0 0 rgba(255,176,0,0); } }
        html { scroll-behavior:smooth; }
        body { -webkit-text-size-adjust:100%; text-rendering:optimizeLegibility; }
        .stApp {
          color:var(--hz-text);
          background:
            linear-gradient(rgba(255,176,0,.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,176,0,.028) 1px, transparent 1px),
            radial-gradient(circle at 12% -12%, rgba(255,176,0,.12), transparent 30%),
            radial-gradient(circle at 84% 4%, rgba(123,160,91,.11), transparent 35%),
            var(--hz-bg);
          background-size:28px 28px,28px 28px,auto,auto,auto;
        }
        .stApp:before {
          content:""; position:fixed; inset:0; pointer-events:none; z-index:999999;
          background:repeating-linear-gradient(0deg, rgba(255,176,0,.035) 0, rgba(255,176,0,.035) 1px, transparent 3px, transparent 6px);
          mix-blend-mode:screen; animation:hz-scan 4s ease-in-out infinite;
        }
        [data-testid="stHeader"] { background:rgba(14,9,5,.84); border-bottom:1px solid var(--hz-line); backdrop-filter:blur(8px); }
        .block-container { max-width:1660px; padding-top:.55rem; padding-bottom:4rem; font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
        h1,h2,h3,h4,p,li,span,div { letter-spacing:.01em; }
        h1,h2,h3,h4 { color:var(--hz-text); text-transform:none; }
        h1 { font-weight:850; }
        p,li { line-height:1.55; }

        .st-key-hz_topbar { position:sticky; top:.42rem; z-index:999900; margin:.05rem 0 .78rem; padding:.45rem; border:1px solid var(--hz-brass); border-radius:0; background:linear-gradient(180deg,#2B1A0D,#130D07); box-shadow:0 16px 46px rgba(0,0,0,.34), inset 0 0 0 1px rgba(255,230,165,.06); }
        .st-key-hz_topbar [data-testid="stHorizontalBlock"] { align-items:center; gap:.36rem!important; }
        .hz-brand-block,.hz-drawer-brand { display:flex; align-items:center; gap:.62rem; min-height:40px; }
        .hz-logo { width:34px; height:34px; display:inline-grid; place-items:center; flex:0 0 34px; border-radius:0; font-size:.7rem; font-weight:950; color:#130D07; background:var(--hz-amber); box-shadow:0 0 20px rgba(255,176,0,.23); }
        .hz-brand-block strong,.hz-drawer-brand strong { display:block; color:var(--hz-text); font-size:.72rem; letter-spacing:.08em; }
        .hz-brand-block small,.hz-drawer-brand small { display:block; color:var(--hz-muted); font-size:.55rem; margin-top:.05rem; letter-spacing:.06em; }
        .hz-top-ticker { position:relative; overflow:hidden; min-height:38px; border:1px solid rgba(255,176,0,.52); background:#090603; display:flex; align-items:center; }
        .hz-top-ticker span { color:var(--hz-amber); font-size:.66rem; font-weight:850; white-space:nowrap; display:inline-block; padding-left:.7rem; animation:hz-ticker 26s linear infinite; }
        .st-key-hz_topbar [data-testid="stPageLink"] a { min-height:38px!important; justify-content:center!important; border-radius:0!important; border:1px solid rgba(197,148,69,.58)!important; color:#E7C579!important; background:#1A1108!important; font-size:.62rem!important; font-weight:850!important; padding:.35rem .28rem!important; text-transform:uppercase; }
        .st-key-hz_topbar [data-testid="stPageLink"] a:hover,.st-key-hz_topbar [data-testid="stPageLink"] a:focus-visible { color:#120C05!important; background:var(--hz-amber)!important; border-color:var(--hz-amber)!important; transform:translateY(-1px); }
        [data-testid="stSidebar"] { background:#120C06; border-right:1px solid var(--hz-brass); box-shadow:18px 0 50px rgba(0,0,0,.28); }
        [data-testid="stSidebar"] > div:first-child { padding-top:.65rem; }
        .hz-drawer-brand { padding:.18rem .18rem .72rem; border-bottom:1px solid var(--hz-line); margin-bottom:.6rem; }
        [data-testid="stSidebar"] [data-testid="stExpander"] { border:1px solid rgba(197,148,69,.44); border-radius:0; background:#1A1108; }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary { color:#DDB96C; font-size:.76rem; }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a { border-radius:0; min-height:40px; color:#E7C579!important; font-size:.72rem!important; border:1px solid rgba(197,148,69,.24); margin:.18rem 0; }
        .hz-runtime { display:flex; align-items:center; gap:.44rem; border-radius:0; padding:.48rem .58rem; font-size:.61rem; font-weight:850; letter-spacing:.08em; border:1px solid var(--hz-line); }
        .hz-runtime span { width:.48rem; height:.48rem; border-radius:50%; background:var(--hz-olive); box-shadow:0 0 18px rgba(123,160,91,.42); }
        .hz-runtime-offline { color:#CFE2A0; background:rgba(123,160,91,.13); }
        .hz-runtime-note { color:#A67C40; font-size:.64rem; line-height:1.4; padding:.34rem .1rem .5rem; }
        .st-key-hz_mobile_nav { display:none; }
        .hz-hero { position:relative; overflow:hidden; border:1px solid var(--hz-brass); border-radius:0; padding:1rem 1.1rem 1.05rem; margin-bottom:.7rem; background:linear-gradient(180deg,#2B1A0D,#130D07); box-shadow:0 16px 44px rgba(0,0,0,.28), inset 0 0 0 1px rgba(255,230,165,.05); }
        .hz-hero:before { content:""; position:absolute; inset:0; background:repeating-linear-gradient(0deg,rgba(255,176,0,.04) 0,rgba(255,176,0,.04) 1px,transparent 4px,transparent 8px); pointer-events:none; }
        .hz-hero:after { content:"READY · VERIFY · ROUTE · PRINT · READY · VERIFY · ROUTE · PRINT"; position:absolute; right:-5%; bottom:.5rem; color:rgba(255,176,0,.08); font-size:2.8rem; font-weight:950; letter-spacing:.08em; white-space:nowrap; }
        .hz-kicker { position:relative; color:var(--hz-amber); font-size:.58rem; font-weight:950; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.34rem; }
        .hz-hero h1 { position:relative; margin:0; font-size:clamp(1.55rem,2.25vw,2.25rem); line-height:1.05; text-transform:uppercase; }
        .hz-hero p { position:relative; margin:.36rem 0 0; color:#D3B06C; max-width:1020px; font-size:.82rem; }
        .hz-hero-meta { position:relative; display:flex; gap:.32rem; flex-wrap:wrap; margin-top:.58rem; }
        .hz-chip { border:1px solid rgba(255,176,0,.54); border-radius:0; padding:.22rem .5rem; color:var(--hz-amber); font-size:.55rem; font-weight:850; background:#120C06; text-transform:uppercase; }
        .hz-context-bar { display:flex; align-items:center; justify-content:space-between; gap:.8rem; flex-wrap:wrap; margin:.25rem 0 .75rem; padding:.6rem .72rem; border:1px solid var(--hz-line); border-radius:0; background:#130D07; }
        .hz-context-title { color:var(--hz-text); font-size:.78rem; font-weight:850; }
        .hz-context-meta { color:#D6A83B; font-size:.66rem; margin-left:.55rem; }
        .hz-context-right { color:#A67C40; font-size:.61rem; letter-spacing:.04em; }
        .hz-section-head { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin:1.05rem 0 .5rem; padding-bottom:.38rem; border-bottom:1px dashed rgba(197,148,69,.42); }
        .hz-section-head h2 { margin:0; color:var(--hz-text); font-size:1.08rem; text-transform:uppercase; }
        .hz-section-head p { margin:.14rem 0 0; color:#B88A45; font-size:.7rem; }
        .hz-section-tag { color:var(--hz-amber); font-size:.58rem; font-weight:900; letter-spacing:.12em; text-transform:uppercase; white-space:nowrap; }
        [data-testid="stMetric"], .hz-kpi-item, .hz-card, .hz-command-card { border:1px solid var(--hz-line)!important; border-radius:0!important; background:#150E08!important; box-shadow:inset 0 0 0 1px rgba(255,230,165,.04)!important; }
        [data-testid="stMetric"] { padding:.9rem .95rem; }
        [data-testid="stMetricValue"] { color:var(--hz-amber); font-weight:900; letter-spacing:.01em; }
        [data-testid="stMetricLabel"] { color:#D3B06C; font-size:.68rem; text-transform:uppercase; }
        .hz-kpi-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(145px,1fr)); gap:.56rem; margin:.14rem 0 .76rem; }
        .hz-kpi-item { min-width:0; padding:.72rem .82rem; animation:hz-pulse 5.5s ease-in-out infinite; }
        .hz-kpi-label { color:#B88A45; font-size:.57rem; font-weight:950; letter-spacing:.075em; text-transform:uppercase; line-height:1.25; }
        .hz-kpi-value { color:var(--hz-amber); font-size:1.28rem; font-weight:950; letter-spacing:.01em; line-height:1.08; margin:.28rem 0 .16rem; overflow-wrap:anywhere; }
        .hz-kpi-detail { color:#A67C40; font-size:.62rem; line-height:1.32; min-height:.82rem; }
        .hz-card { position:relative; min-height:105px; padding:.86rem .92rem; }
        .hz-card:before,.hz-command-card:before { content:""; position:absolute; left:0; top:0; bottom:0; width:3px; background:var(--hz-brass); }
        .hz-card .label { color:#B88A45; font-size:.57rem; font-weight:950; letter-spacing:.1em; text-transform:uppercase; }
        .hz-card .value { color:var(--hz-text); font-size:1rem; font-weight:850; margin:.27rem 0; }
        .hz-card .detail { color:#C9A86A; font-size:.72rem; line-height:1.43; }
        .hz-command-card { position:relative; padding:1rem; }
        .hz-command-card.critical { border-color:rgba(182,64,36,.78)!important; box-shadow:inset 3px 0 0 var(--hz-red),0 0 22px rgba(182,64,36,.18)!important; }
        .hz-command-card.high { border-color:rgba(199,119,30,.72)!important; box-shadow:inset 3px 0 0 var(--hz-amber),0 0 22px rgba(255,176,0,.12)!important; }
        .hz-command-eyebrow { color:#B88A45; font-size:.58rem; font-weight:950; letter-spacing:.12em; text-transform:uppercase; }
        .hz-command-title { color:var(--hz-text); font-size:1.38rem; font-weight:950; letter-spacing:.01em; margin:.24rem 0 .16rem; text-transform:uppercase; }
        .hz-command-copy { color:#D3B06C; font-size:.74rem; line-height:1.47; }
        .hz-gate { display:flex; align-items:center; gap:.55rem; padding:.62rem .68rem; border-radius:0; border:1px solid var(--hz-line); background:#150E08; margin:.4rem 0; }
        .hz-gate-dot { width:.54rem; height:.54rem; border-radius:50%; background:var(--hz-olive); box-shadow:0 0 18px rgba(123,160,91,.45); flex:0 0 auto; }
        .hz-gate.warn .hz-gate-dot { background:var(--hz-amber); box-shadow:0 0 18px rgba(255,176,0,.48); animation:hz-blink 1.2s steps(2,end) infinite; }
        .hz-gate.danger .hz-gate-dot { background:var(--hz-red); box-shadow:0 0 18px rgba(182,64,36,.55); animation:hz-blink .85s steps(2,end) infinite; }
        .hz-gate strong { display:block; color:var(--hz-text); font-size:.72rem; text-transform:uppercase; }
        .hz-gate span { display:block; color:#C9A86A; font-size:.62rem; margin-top:.03rem; }
        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] { border:1px solid var(--hz-line); border-radius:0; overflow:hidden; background:#150E08; box-shadow:none; max-width:100%; }
        iframe[title="streamlit_folium.st_folium"] { border:1px solid var(--hz-brass)!important; border-radius:0!important; box-shadow:0 12px 38px rgba(0,0,0,.26)!important; overflow:hidden; max-width:100%!important; filter:saturate(.72) sepia(.18) contrast(1.05); }
        [data-testid="stAlert"] { border-radius:0; border-width:1px; font-size:.82rem; }
        [data-testid="stExpander"] { border:1px solid var(--hz-line); border-radius:0; background:#150E08; overflow:hidden; }
        .stTabs [data-baseweb="tab-list"] { gap:.2rem; border-bottom:1px solid var(--hz-line); }
        .stTabs [data-baseweb="tab"] { border-radius:0; padding:.46rem .7rem; font-size:.76rem; text-transform:uppercase; }
        .stTabs [aria-selected="true"] { background:#2B1A0D; box-shadow:inset 0 -2px 0 var(--hz-amber); color:var(--hz-amber); }
        .stButton > button, .stDownloadButton > button { border-radius:0; min-height:2.55rem; font-weight:850; border:1px solid rgba(255,176,0,.62); background:#2B1A0D; color:var(--hz-text); transition:all .14s ease; text-transform:uppercase; }
        .stButton > button:hover, .stDownloadButton > button:hover { transform:translateY(-1px); border-color:var(--hz-amber); background:var(--hz-amber); color:#130D07; box-shadow:0 10px 24px rgba(0,0,0,.22); }
        [data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"], [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { border-radius:0!important; border-color:rgba(197,148,69,.46)!important; background:#120C06!important; color:var(--hz-text)!important; }
        .hz-mode { display:inline-flex; align-items:center; gap:.38rem; border-radius:0; padding:.27rem .58rem; font-size:.59rem; font-weight:950; letter-spacing:.055em; text-transform:uppercase; }
        .hz-dot { width:.42rem; height:.42rem; border-radius:50%; box-shadow:0 0 14px currentColor; }
        .hz-risk { display:inline-flex; color:#120C06; border-radius:0; padding:.25rem .58rem; font-size:.64rem; font-weight:950; letter-spacing:.045em; box-shadow:inset 0 0 0 1px rgba(255,230,165,.18); }
        .hz-disclaimer { color:#A67C40; font-size:.64rem; border-top:1px dashed var(--hz-line); margin-top:1.6rem; padding-top:.8rem; }
        hr { border-color:var(--hz-line)!important; }
        @media (max-width:1050px) { .st-key-hz_topbar .hz-brand-block small { display:none; } .st-key-hz_topbar [data-testid="stPageLink"] a { font-size:.56rem!important; padding:.3rem .2rem!important; } .block-container { padding-left:.78rem; padding-right:.78rem; } }
        @media (max-width:900px) { .st-key-hz_topbar { display:none!important; } .block-container { padding-left:.8rem; padding-right:.8rem; padding-top:.72rem; } [data-testid="stSidebar"] { width:min(84vw,320px)!important; min-width:min(84vw,320px)!important; } .hz-hero { padding:.85rem .9rem; } }
        @media (max-width:720px) {
          .block-container { padding:.62rem .62rem 6.15rem; }
          [data-testid="stHorizontalBlock"] { flex-direction:column!important; gap:.6rem!important; }
          [data-testid="stHorizontalBlock"] > [data-testid="column"] { width:100%!important; flex:1 1 100%!important; min-width:0!important; }
          .hz-hero h1 { font-size:1.34rem; }
          .hz-hero p { font-size:.77rem; }
          .hz-context-bar { align-items:flex-start; padding:.48rem .55rem; }
          .hz-context-right { width:100%; }
          .hz-section-head { align-items:flex-start; margin:.8rem 0 .4rem; }
          .hz-section-tag { display:none; }
          .hz-kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:.46rem; }
          iframe[title="streamlit_folium.st_folium"] { min-height:390px!important; height:58vh!important; }
          .stButton > button, .stDownloadButton > button { min-height:46px; width:100%; font-size:.82rem; }
          [data-testid="stPageLink"] a { min-height:46px!important; display:flex!important; align-items:center!important; }
          [data-baseweb="select"] > div, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input { min-height:46px; }
          .st-key-hz_mobile_nav { display:block!important; position:fixed; left:max(.45rem,env(safe-area-inset-left)); right:max(.45rem,env(safe-area-inset-right)); bottom:max(.38rem,env(safe-area-inset-bottom)); z-index:999990; padding:.26rem; border:1px solid var(--hz-brass); border-radius:0; background:#120C06; box-shadow:0 16px 48px rgba(0,0,0,.46); }
          .st-key-hz_mobile_nav [data-testid="stHorizontalBlock"] { flex-direction:row!important; gap:.16rem!important; align-items:stretch!important; }
          .st-key-hz_mobile_nav [data-testid="stHorizontalBlock"] > [data-testid="column"] { width:25%!important; flex:1 1 25%!important; min-width:0!important; }
          .st-key-hz_mobile_nav [data-testid="stPageLink"] a { min-height:54px!important; justify-content:center!important; text-align:center; padding:.32rem .1rem!important; border-radius:0!important; border:1px solid rgba(197,148,69,.30); color:#E7C579!important; background:#1A1108; font-size:.58rem!important; font-weight:850!important; line-height:1.18!important; white-space:pre-line!important; }
          .st-key-hz_mobile_nav [data-testid="stPageLink"] a:hover { color:#120C05!important; background:var(--hz-amber)!important; }
        }
        @media (max-width:480px) { .hz-hero-meta .hz-chip:nth-child(n+3) { display:none; } [data-testid="stSidebar"] { width:88vw!important; min-width:88vw!important; } .st-key-hz_mobile_nav { left:.32rem; right:.32rem; bottom:max(.28rem,env(safe-area-inset-bottom)); } .st-key-hz_mobile_nav [data-testid="stPageLink"] a { font-size:.55rem!important; min-height:52px!important; } }
        @media (pointer:coarse) { .stButton > button, .stDownloadButton > button, [data-testid="stPageLink"] a { min-height:48px!important; } [data-baseweb="select"] > div { min-height:46px; } }
        @media (prefers-reduced-motion:reduce) { *,*:before,*:after { transition:none!important; animation:none!important; scroll-behavior:auto!important; } }
        </style>
        """,
        unsafe_allow_html=True,
    )
    _render_navigation()
    _render_mobile_navigation()


def render_page_header(title: str, description: str) -> None:
    st.markdown(
        "<section class='hz-hero'>"
        "<div class='hz-kicker'>Dynamic retro dispatch board</div>"
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(description)}</p>"
        "<div class='hz-hero-meta'>"
        "<span class='hz-chip'>Amber CRT</span>"
        "<span class='hz-chip'>Capacity gated</span>"
        "<span class='hz-chip'>Route pulse</span>"
        "<span class='hz-chip'>Decision support only</span>"
        "</div>"
        "</section>",
        unsafe_allow_html=True,
    )


def render_context_bar(title: str, meta: str, trailing: str = "") -> None:
    st.markdown(
        "<div class='hz-context-bar'>"
        "<div class='hz-context-left'>"
        f"<span class='hz-context-title'>{html.escape(str(title))}</span>"
        f"<span class='hz-context-meta'>{html.escape(str(meta))}</span>"
        "</div>"
        f"<div class='hz-context-right'>{html.escape(str(trailing))}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_section_header(title: str, description: str = "", tag: str = "") -> None:
    st.markdown(
        "<div class='hz-section-head'><div>"
        f"<h2>{html.escape(str(title))}</h2>"
        f"<p>{html.escape(str(description))}</p>"
        "</div>"
        f"<span class='hz-section-tag'>{html.escape(str(tag))}</span>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_decision_gate(title: str, detail: str, state: str = "ok") -> None:
    css_state = "danger" if state == "danger" else "warn" if state == "warn" else ""
    st.markdown(
        f"<div class='hz-gate {css_state}'><span class='hz-gate-dot'></span><div>"
        f"<strong>{html.escape(str(title))}</strong><span>{html.escape(str(detail))}</span>"
        "</div></div>",
        unsafe_allow_html=True,
    )


def render_command_card(eyebrow: str, title: str, detail: str, severity: str = "") -> None:
    severity_class = str(severity).lower() if str(severity).lower() in {"critical", "high"} else ""
    st.markdown(
        f"<div class='hz-command-card {severity_class}'>"
        f"<div class='hz-command-eyebrow'>{html.escape(str(eyebrow))}</div>"
        f"<div class='hz-command-title'>{html.escape(str(title))}</div>"
        f"<div class='hz-command-copy'>{html.escape(str(detail))}</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_data_mode_indicator(mode: str = "DEMO") -> None:
    mode = str(mode).upper()
    label = {"LIVE": "LIVE DATA", "CACHED": "CACHED DATA", "DEMO": "DEMONSTRATION DATA"}.get(mode, mode)
    foreground, background = MODE_COLORS.get(mode, ("#C9A86A", "rgba(201,168,106,.10)"))
    st.markdown(
        f"<span class='hz-mode' style='color:{foreground};background:{background};border:1px solid {foreground}88'><span class='hz-dot' style='background:{foreground}'></span>{html.escape(label)}</span>",
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
        st.markdown("### Incident scope")
        city = st.selectbox("Geography", DEMO_CITY_OPTIONS, key=f"{prefix}_city")
        label = st.selectbox("Hazard profile", list(HAZARD_PROFILE_OPTIONS), key=f"{prefix}_hazard")
        st.caption("Demo values are synthetic unless an authoritative source is explicitly activated.")
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
    text_color = "#120C05" if level in {"LOW", "MODERATE", "HIGH"} else "#FFE6A5"
    st.markdown(
        f"<span class='hz-risk' style='background:{color};color:{text_color}'>{html.escape(level)}</span>",
        unsafe_allow_html=True,
    )


def render_kpi_strip(metrics: list[tuple[str, object, str | None]]) -> None:
    if not metrics:
        return
    cards = []
    for label, value, help_text in metrics:
        safe_label = html.escape(str(label))
        safe_value = html.escape(str(value))
        detail = html.escape(str(help_text)) if help_text else ""
        cards.append(
            "<div class='hz-kpi-item' role='group' aria-label='" + html.escape(str(label), quote=True) + "'>"
            f"<div class='hz-kpi-label'>{safe_label}</div>"
            f"<div class='hz-kpi-value'>{safe_value}</div>"
            f"<div class='hz-kpi-detail'>{detail}</div>"
            "</div>"
        )
    st.markdown(
        "<div class='hz-kpi-grid' role='group' aria-label='Key metrics'>" + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def render_empty_state(message: str) -> None:
    st.info(message)


def render_disclaimer() -> None:
    st.markdown(
        "<div class='hz-disclaimer'>Decision-support system only. Evacuation, relocation and emergency orders remain with authorized disaster-management officials. Bundled operational values are demonstration data unless an authoritative source is explicitly identified.</div>",
        unsafe_allow_html=True,
    )
