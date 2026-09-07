import html

import streamlit as st

from src.runtime_mode import offline_mode


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

# Desktop navigation lives in the command bar. The sidebar is deliberately a
# contextual control drawer, not the product's information architecture.
CORE_NAV = [
    ("Command", "app.py", "⌂"),
    ("Hazard Map", "pages/2_Red_Zone_Map.py", "◉"),
    ("Risk", "pages/3_Risk_Analysis.py", "◒"),
    ("Relocate", "pages/4_Relocation_Planner.py", "⇢"),
    ("Briefing", "pages/13_Briefing.py", "▤"),
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
    """Render a persistent desktop command bar and a small sidebar tool drawer."""
    with st.container(key="hz_topbar"):
        brand, nav1, nav2, nav3, nav4, nav5 = st.columns([1.55, 1, 1, 1, 1, 1], gap="small")
        with brand:
            st.markdown(
                "<div class='hz-top-brand'><span class='hz-top-logo'>HZ</span>"
                "<span><strong>HAZARD COMMAND</strong><small>SIH26191</small></span></div>",
                unsafe_allow_html=True,
            )
        for column, (label, path, icon) in zip([nav1, nav2, nav3, nav4, nav5], CORE_NAV):
            with column:
                st.page_link(path, label=f"{icon}  {label}", use_container_width=True)

    with st.sidebar:
        st.markdown(
            "<div class='hz-drawer-brand'><span class='hz-top-logo'>HZ</span>"
            "<span><strong>CONTROL DRAWER</strong><small>Incident context & tools</small></span></div>",
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
        st.caption("Decision support · source aware · capacity constrained")


def _render_mobile_navigation() -> None:
    """Render four high-frequency field actions; CSS exposes them only on phones."""
    with st.container(key="hz_mobile_nav"):
        columns = st.columns(len(MOBILE_NAV), gap="small")
        for column, (label, path, icon) in zip(columns, MOBILE_NAV):
            with column:
                st.page_link(path, label=f"{icon} {label}", use_container_width=True)


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --hz-bg:#05080D;
          --hz-panel:#0B111A;
          --hz-panel-2:#101925;
          --hz-panel-3:#152131;
          --hz-line:rgba(157,178,201,.13);
          --hz-line-strong:rgba(91,169,255,.34);
          --hz-text:#F4F7FB;
          --hz-muted:#8D9CAF;
          --hz-dim:#607287;
          --hz-blue:#5BA9FF;
          --hz-cyan:#49D7C8;
          --hz-shadow:0 20px 60px rgba(0,0,0,.30);
        }
        html { scroll-behavior:smooth; }
        body { -webkit-text-size-adjust:100%; text-rendering:optimizeLegibility; }
        .stApp {
          color:var(--hz-text);
          background:
            linear-gradient(rgba(255,255,255,.012) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,.012) 1px, transparent 1px),
            radial-gradient(circle at 76% -12%, rgba(73,215,200,.07), transparent 31%),
            radial-gradient(circle at 18% -8%, rgba(91,169,255,.10), transparent 35%),
            var(--hz-bg);
          background-size:44px 44px,44px 44px,auto,auto,auto;
        }
        [data-testid="stHeader"] {
          background:rgba(5,8,13,.82);
          border-bottom:1px solid rgba(255,255,255,.035);
          backdrop-filter:blur(18px);
        }
        .block-container { max-width:1640px; padding-top:.55rem; padding-bottom:4rem; }
        h1,h2,h3,h4 { letter-spacing:-.035em; }
        h1 { font-weight:820; }
        h2 { font-size:1.28rem; margin-top:1.2rem; }
        h3 { font-size:1rem; }
        p,li { line-height:1.55; }

        /* desktop command bar */
        .st-key-hz_topbar {
          position:sticky;
          top:.38rem;
          z-index:999900;
          padding:.36rem .42rem;
          margin:.05rem 0 .8rem;
          border:1px solid var(--hz-line);
          border-radius:15px;
          background:rgba(7,11,17,.90);
          backdrop-filter:blur(20px);
          -webkit-backdrop-filter:blur(20px);
          box-shadow:0 12px 38px rgba(0,0,0,.28);
        }
        .st-key-hz_topbar [data-testid="stHorizontalBlock"] { align-items:center; gap:.28rem!important; }
        .st-key-hz_topbar [data-testid="stPageLink"] a {
          min-height:38px!important;
          justify-content:center!important;
          border-radius:10px!important;
          border:1px solid transparent!important;
          color:#AEBBC9!important;
          font-size:.76rem!important;
          font-weight:720!important;
          padding:.35rem .5rem!important;
          transition:all .15s ease;
        }
        .st-key-hz_topbar [data-testid="stPageLink"] a:hover,
        .st-key-hz_topbar [data-testid="stPageLink"] a:focus-visible {
          color:#F5F8FB!important;
          background:rgba(91,169,255,.09)!important;
          border-color:rgba(91,169,255,.20)!important;
        }
        .hz-top-brand,.hz-drawer-brand { display:flex; align-items:center; gap:.58rem; min-height:38px; }
        .hz-top-logo {
          width:31px; height:31px; display:inline-grid; place-items:center; flex:0 0 31px;
          border-radius:9px; font-size:.65rem; font-weight:950; color:#041018;
          background:linear-gradient(135deg,#73B9FF,#49D7C8);
          box-shadow:0 8px 24px rgba(91,169,255,.22);
        }
        .hz-top-brand strong,.hz-drawer-brand strong { display:block; color:#F2F6FA; font-size:.71rem; letter-spacing:.08em; }
        .hz-top-brand small,.hz-drawer-brand small { display:block; color:#65778B; font-size:.56rem; margin-top:.04rem; letter-spacing:.06em; }

        /* sidebar becomes a contextual drawer, not primary navigation */
        [data-testid="stSidebar"] {
          background:linear-gradient(180deg,#090E15,#070B11);
          border-right:1px solid var(--hz-line);
          box-shadow:18px 0 52px rgba(0,0,0,.22);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top:.6rem; }
        .hz-drawer-brand { padding:.1rem .15rem .7rem; border-bottom:1px solid var(--hz-line); margin-bottom:.55rem; }
        [data-testid="stSidebar"] [data-testid="stExpander"] { border:1px solid rgba(157,178,201,.09); background:rgba(255,255,255,.012); }
        [data-testid="stSidebar"] [data-testid="stExpander"] summary { color:#8EA0B3; font-size:.76rem; }
        [data-testid="stSidebar"] [data-testid="stPageLink"] a {
          border-radius:9px; min-height:38px; color:#B7C4D2!important; font-size:.78rem!important;
        }
        .hz-runtime { display:flex; align-items:center; gap:.42rem; border-radius:9px; padding:.48rem .58rem; font-size:.61rem; font-weight:850; letter-spacing:.08em; }
        .hz-runtime span { width:.43rem; height:.43rem; border-radius:50%; background:#F7C948; box-shadow:0 0 0 4px rgba(247,201,72,.08); }
        .hz-runtime-offline { color:#F7D66B; background:rgba(247,201,72,.07); border:1px solid rgba(247,201,72,.20); }
        .hz-runtime-note { color:#718397; font-size:.64rem; line-height:1.4; padding:.34rem .1rem .5rem; }

        /* mobile action bar is hidden on desktop/tablet */
        .st-key-hz_mobile_nav { display:none; }

        /* compact page identity */
        .hz-hero {
          position:relative; overflow:hidden; border:1px solid var(--hz-line);
          border-radius:17px; padding:.95rem 1.1rem 1rem;
          background:linear-gradient(112deg,rgba(91,169,255,.095),rgba(11,17,26,.74) 46%,rgba(73,215,200,.035));
          box-shadow:0 12px 42px rgba(0,0,0,.18); margin-bottom:.68rem;
        }
        .hz-hero:after { content:""; position:absolute; width:170px; height:170px; right:-75px; top:-100px; border-radius:50%; border:1px solid rgba(91,169,255,.13); box-shadow:0 0 0 28px rgba(91,169,255,.02),0 0 0 58px rgba(73,215,200,.012); }
        .hz-kicker { color:#76A6D3; font-size:.58rem; font-weight:850; letter-spacing:.16em; text-transform:uppercase; margin-bottom:.28rem; }
        .hz-hero h1 { margin:0; font-size:clamp(1.35rem,2vw,1.9rem); line-height:1.12; position:relative; z-index:1; }
        .hz-hero p { margin:.32rem 0 0; color:#98A9BA; max-width:1020px; font-size:.82rem; position:relative; z-index:1; }
        .hz-hero-meta { display:flex; gap:.32rem; flex-wrap:wrap; margin-top:.55rem; position:relative; z-index:1; }
        .hz-chip { border:1px solid rgba(157,178,201,.14); border-radius:999px; padding:.21rem .48rem; color:#8396AA; font-size:.55rem; font-weight:760; background:rgba(4,8,13,.22); }

        /* operational ribbons */
        .hz-context-bar {
          display:flex; align-items:center; justify-content:space-between; gap:.8rem; flex-wrap:wrap;
          margin:.25rem 0 .7rem; padding:.55rem .7rem; border:1px solid var(--hz-line);
          border-radius:12px; background:rgba(11,17,26,.72);
        }
        .hz-context-left { display:flex; align-items:center; gap:.48rem; flex-wrap:wrap; }
        .hz-context-title { color:#EAF0F6; font-size:.78rem; font-weight:760; }
        .hz-context-meta { color:#75889C; font-size:.66rem; }
        .hz-context-right { color:#5F7489; font-size:.61rem; letter-spacing:.04em; }
        .hz-section-head { display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; margin:1rem 0 .48rem; }
        .hz-section-head h2 { margin:0; color:#F2F6FA; font-size:1.08rem; }
        .hz-section-head p { margin:.14rem 0 0; color:#74869A; font-size:.7rem; }
        .hz-section-tag { color:#7890A8; font-size:.58rem; font-weight:800; letter-spacing:.12em; text-transform:uppercase; white-space:nowrap; }

        /* data surfaces */
        [data-testid="stMetric"] {
          background:linear-gradient(145deg,rgba(255,255,255,.036),rgba(255,255,255,.009));
          border:1px solid var(--hz-line); border-radius:14px; padding:.9rem .95rem;
          box-shadow:0 8px 24px rgba(0,0,0,.10);
        }
        [data-testid="stMetricValue"] { font-weight:820; letter-spacing:-.045em; }
        [data-testid="stMetricLabel"] { color:#8496A8; font-size:.7rem; }
        .hz-kpi-grid {
          display:grid;
          grid-template-columns:repeat(auto-fit,minmax(145px,1fr));
          gap:.56rem;
          margin:.14rem 0 .72rem;
        }
        .hz-kpi-item {
          min-width:0; border:1px solid var(--hz-line); border-radius:13px; padding:.72rem .82rem;
          background:linear-gradient(145deg,rgba(255,255,255,.032),rgba(255,255,255,.008));
          box-shadow:0 8px 24px rgba(0,0,0,.09);
        }
        .hz-kpi-label { color:#7E91A5; font-size:.58rem; font-weight:850; letter-spacing:.075em; text-transform:uppercase; line-height:1.25; }
        .hz-kpi-value { color:#F4F7FB; font-size:1.28rem; font-weight:850; letter-spacing:-.045em; line-height:1.08; margin:.28rem 0 .16rem; overflow-wrap:anywhere; }
        .hz-kpi-detail { color:#667B90; font-size:.62rem; line-height:1.32; min-height:.82rem; }
        .hz-card { position:relative; min-height:105px; border:1px solid var(--hz-line); border-radius:14px; padding:.86rem .92rem; background:linear-gradient(145deg,rgba(255,255,255,.029),rgba(255,255,255,.007)); }
        .hz-card .label { color:#758A9F; font-size:.57rem; font-weight:850; letter-spacing:.1em; text-transform:uppercase; }
        .hz-card .value { color:#F1F5F9; font-size:1rem; font-weight:780; margin:.27rem 0; }
        .hz-card .detail { color:#8899AA; font-size:.72rem; line-height:1.43; }
        .hz-command-card { border:1px solid var(--hz-line); border-radius:16px; padding:1rem; background:rgba(10,16,25,.78); box-shadow:0 12px 36px rgba(0,0,0,.14); }
        .hz-command-card.critical { border-color:rgba(255,93,115,.32); box-shadow:inset 3px 0 0 rgba(255,93,115,.82),0 12px 36px rgba(0,0,0,.14); }
        .hz-command-card.high { border-color:rgba(255,159,67,.28); box-shadow:inset 3px 0 0 rgba(255,159,67,.78),0 12px 36px rgba(0,0,0,.14); }
        .hz-command-eyebrow { color:#73879B; font-size:.58rem; font-weight:850; letter-spacing:.12em; text-transform:uppercase; }
        .hz-command-title { color:#F4F7FB; font-size:1.38rem; font-weight:840; letter-spacing:-.035em; margin:.24rem 0 .16rem; }
        .hz-command-copy { color:#889AAC; font-size:.74rem; line-height:1.47; }
        .hz-gate { display:flex; align-items:center; gap:.55rem; padding:.62rem .68rem; border-radius:11px; border:1px solid var(--hz-line); background:rgba(255,255,255,.014); margin:.4rem 0; }
        .hz-gate-dot { width:.52rem; height:.52rem; border-radius:50%; background:#49D7C8; box-shadow:0 0 0 4px rgba(73,215,200,.07); flex:0 0 auto; }
        .hz-gate.warn .hz-gate-dot { background:#F7C948; box-shadow:0 0 0 4px rgba(247,201,72,.07); }
        .hz-gate.danger .hz-gate-dot { background:#FF5D73; box-shadow:0 0 0 4px rgba(255,93,115,.07); }
        .hz-gate strong { display:block; color:#DDE6EE; font-size:.72rem; }
        .hz-gate span { display:block; color:#708397; font-size:.62rem; margin-top:.03rem; }

        [data-testid="stDataFrame"], [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {
          border:1px solid var(--hz-line); border-radius:14px; overflow:hidden; background:rgba(255,255,255,.009); box-shadow:none; max-width:100%;
        }
        iframe[title="streamlit_folium.st_folium"] { border:1px solid var(--hz-line)!important; border-radius:15px!important; box-shadow:0 12px 38px rgba(0,0,0,.16)!important; overflow:hidden; max-width:100%!important; }
        [data-testid="stAlert"] { border-radius:11px; border-width:1px; font-size:.82rem; }
        [data-testid="stExpander"] { border:1px solid var(--hz-line); border-radius:11px; background:rgba(255,255,255,.011); overflow:hidden; }
        .stTabs [data-baseweb="tab-list"] { gap:.2rem; border-bottom:1px solid var(--hz-line); }
        .stTabs [data-baseweb="tab"] { border-radius:8px 8px 0 0; padding:.46rem .7rem; font-size:.78rem; }
        .stTabs [aria-selected="true"] { background:rgba(91,169,255,.065); box-shadow:inset 0 -2px 0 var(--hz-blue); }
        .stButton > button, .stDownloadButton > button {
          border-radius:10px; min-height:2.45rem; font-weight:720; border:1px solid rgba(91,169,255,.25);
          background:linear-gradient(180deg,rgba(91,169,255,.13),rgba(91,169,255,.045)); transition:all .14s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover { transform:translateY(-1px); border-color:rgba(91,169,255,.52); box-shadow:0 10px 24px rgba(0,0,0,.16); }
        [data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"], [data-testid="stNumberInput"] input, [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { border-radius:10px!important; border-color:rgba(157,178,201,.18)!important; background:rgba(255,255,255,.022)!important; }
        .hz-mode { display:inline-flex; align-items:center; gap:.38rem; border-radius:999px; padding:.27rem .58rem; font-size:.59rem; font-weight:850; letter-spacing:.055em; }
        .hz-dot { width:.4rem; height:.4rem; border-radius:50%; }
        .hz-risk { display:inline-flex; color:#fff; border-radius:999px; padding:.25rem .58rem; font-size:.64rem; font-weight:850; letter-spacing:.045em; box-shadow:inset 0 0 0 1px rgba(255,255,255,.16); }
        .hz-disclaimer { color:#66798C; font-size:.64rem; border-top:1px solid var(--hz-line); margin-top:1.6rem; padding-top:.8rem; }
        hr { border-color:var(--hz-line)!important; }

        @media (max-width:1050px) {
          .st-key-hz_topbar .hz-top-brand small { display:none; }
          .st-key-hz_topbar [data-testid="stPageLink"] a { font-size:.68rem!important; padding:.3rem .28rem!important; }
          .block-container { padding-left:.78rem; padding-right:.78rem; }
        }

        /* tablet */
        @media (max-width:900px) {
          .st-key-hz_topbar { display:none!important; }
          .block-container { padding-left:.8rem; padding-right:.8rem; padding-top:.72rem; }
          [data-testid="stSidebar"] { width:min(84vw,320px)!important; min-width:min(84vw,320px)!important; }
          .hz-hero { border-radius:14px; padding:.85rem .9rem; }
          .hz-card { min-height:0; }
        }

        /* phone */
        @media (max-width:720px) {
          .block-container { padding:.62rem .62rem 6.15rem; }
          [data-testid="stHorizontalBlock"] { flex-direction:column!important; gap:.6rem!important; }
          [data-testid="stHorizontalBlock"] > [data-testid="column"] { width:100%!important; flex:1 1 100%!important; min-width:0!important; }
          .hz-hero { margin-bottom:.55rem; border-radius:13px; padding:.78rem .8rem; box-shadow:none; }
          .hz-hero h1 { font-size:1.34rem; line-height:1.12; }
          .hz-hero p { font-size:.77rem; line-height:1.45; }
          .hz-kicker { font-size:.54rem; margin-bottom:.26rem; }
          .hz-hero-meta { margin-top:.48rem; gap:.25rem; }
          .hz-chip { font-size:.53rem; padding:.19rem .4rem; }
          .hz-context-bar { align-items:flex-start; border-radius:10px; padding:.48rem .55rem; }
          .hz-context-right { width:100%; }
          .hz-section-head { align-items:flex-start; margin:.8rem 0 .4rem; }
          .hz-section-tag { display:none; }
          h2 { font-size:1.06rem; margin-top:.95rem; }
          h3 { font-size:.93rem; }
          p,li { line-height:1.5; }
          [data-testid="stMetric"] { border-radius:12px; padding:.72rem .78rem; min-height:82px; }
          [data-testid="stMetricValue"] { font-size:1.25rem; }
          .hz-kpi-grid { grid-template-columns:repeat(2,minmax(0,1fr)); gap:.46rem; margin:.1rem 0 .68rem; }
          .hz-kpi-item { border-radius:11px; padding:.64rem .68rem; box-shadow:none; }
          .hz-kpi-label { font-size:.54rem; letter-spacing:.045em; }
          .hz-kpi-value { font-size:1.08rem; margin:.25rem 0 .14rem; }
          .hz-kpi-detail { font-size:.58rem; min-height:0; }
          .hz-command-title { font-size:1.18rem; }
          [data-testid="stDataFrame"], [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] { border-radius:12px; overflow-x:auto; }
          iframe[title="streamlit_folium.st_folium"] { border-radius:12px!important; min-height:390px!important; height:58vh!important; box-shadow:none!important; }
          .stTabs [data-baseweb="tab-list"] { overflow-x:auto; overflow-y:hidden; flex-wrap:nowrap; scrollbar-width:none; -webkit-overflow-scrolling:touch; }
          .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display:none; }
          .stTabs [data-baseweb="tab"] { flex:0 0 auto; white-space:nowrap; min-height:44px; }
          .stButton > button, .stDownloadButton > button { min-height:46px; width:100%; font-size:.88rem; }
          [data-testid="stPageLink"] a { min-height:46px!important; display:flex!important; align-items:center!important; }
          [data-baseweb="select"] > div, [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input { min-height:46px; }
          [data-testid="stFileUploaderDropzone"] { padding:.78rem!important; }
          [data-testid="stAlert"] { font-size:.82rem; }
          .hz-disclaimer { font-size:.63rem; margin-top:1.2rem; }

          .st-key-hz_mobile_nav {
            display:block!important;
            position:fixed;
            left:max(.45rem,env(safe-area-inset-left));
            right:max(.45rem,env(safe-area-inset-right));
            bottom:max(.38rem,env(safe-area-inset-bottom));
            z-index:999990;
            padding:.26rem;
            border:1px solid rgba(157,178,201,.19);
            border-radius:15px;
            background:rgba(7,11,17,.95);
            backdrop-filter:blur(18px);
            -webkit-backdrop-filter:blur(18px);
            box-shadow:0 16px 48px rgba(0,0,0,.46);
          }
          .st-key-hz_mobile_nav [data-testid="stHorizontalBlock"] { flex-direction:row!important; gap:.16rem!important; align-items:stretch!important; }
          .st-key-hz_mobile_nav [data-testid="stHorizontalBlock"] > [data-testid="column"] { width:25%!important; flex:1 1 25%!important; min-width:0!important; }
          .st-key-hz_mobile_nav [data-testid="stPageLink"] a {
            min-height:54px!important; height:100%; justify-content:center!important; text-align:center;
            padding:.32rem .1rem!important; border-radius:11px!important; border:1px solid transparent;
            color:#C9D5E1!important; background:transparent; font-size:.64rem!important; font-weight:760!important;
            line-height:1.18!important; white-space:normal!important;
          }
          .st-key-hz_mobile_nav [data-testid="stPageLink"] a:hover,
          .st-key-hz_mobile_nav [data-testid="stPageLink"] a:focus-visible { color:#F5F9FD!important; background:rgba(91,169,255,.10)!important; border-color:rgba(91,169,255,.22)!important; transform:none!important; }
          .st-key-hz_mobile_nav [data-testid="stPageLink"] p { margin:0!important; font-size:inherit!important; line-height:inherit!important; }
        }

        @media (max-width:480px) {
          .hz-hero-meta .hz-chip:nth-child(n+3) { display:none; }
          [data-testid="stSidebar"] { width:88vw!important; min-width:88vw!important; }
          .st-key-hz_mobile_nav { left:.32rem; right:.32rem; bottom:max(.28rem,env(safe-area-inset-bottom)); border-radius:14px; }
          .st-key-hz_mobile_nav [data-testid="stPageLink"] a { font-size:.61rem!important; min-height:52px!important; }
        }
        @media (pointer:coarse) {
          .stButton > button, .stDownloadButton > button, [data-testid="stPageLink"] a { min-height:48px!important; }
          [data-baseweb="select"] > div { min-height:46px; }
        }
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
        "<div class='hz-kicker'>Operational decision workspace</div>"
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(description)}</p>"
        "<div class='hz-hero-meta'><span class='hz-chip'>SIH26191</span><span class='hz-chip'>Explainable risk</span><span class='hz-chip'>Capacity constrained</span></div>"
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
    st.markdown(f"<span class='hz-risk' style='background:{color}'>{html.escape(level)}</span>", unsafe_allow_html=True)


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
