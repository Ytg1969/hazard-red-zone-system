import streamlit as st


RISK_COLORS = {
    "LOW": "#34a853",
    "MODERATE": "#f9ab00",
    "HIGH": "#ea8600",
    "CRITICAL": "#dc3545",
}


def inject_global_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --eoc-bg: #0f1419;
            --eoc-surface: #171d26;
            --eoc-elevated: #202733;
            --eoc-border: #2d3745;
            --eoc-text: #e8eaed;
            --eoc-muted: #98a2b3;
            --eoc-accent: #4a9eff;
        }
        .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
        h1, h2, h3 { letter-spacing: -0.02em; }
        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.025);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }
        .eoc-page-header {
            border-bottom: 1px solid rgba(128,128,128,.25);
            padding-bottom: .8rem;
            margin-bottom: 1.1rem;
        }
        .eoc-page-header h1 { margin: 0; font-size: 1.65rem; }
        .eoc-page-header p { margin: .35rem 0 0; color: #98a2b3; }
        .eoc-mode {
            display: inline-block;
            border: 1px solid rgba(128,128,128,.35);
            border-radius: 999px;
            padding: .18rem .55rem;
            font-size: .75rem;
            font-weight: 600;
            letter-spacing: .03em;
        }
        .eoc-risk-badge {
            display: inline-block;
            color: white;
            border-radius: 999px;
            padding: .2rem .55rem;
            font-size: .78rem;
            font-weight: 700;
        }
        .eoc-panel {
            border: 1px solid rgba(128,128,128,.25);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: .75rem;
        }
        .eoc-disclaimer {
            color: #98a2b3;
            font-size: .78rem;
            border-top: 1px solid rgba(128,128,128,.2);
            margin-top: 1.5rem;
            padding-top: .75rem;
        }
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
    label = {
        "LIVE": "LIVE DATA",
        "CACHED": "CACHED DATA",
        "DEMO": "DEMONSTRATION DATA",
    }.get(mode, mode)
    st.markdown(f"<span class='eoc-mode'>{label}</span>", unsafe_allow_html=True)


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
        "<div class='eoc-disclaimer'>Decision-support prototype only. "
        "Final evacuation, relocation and emergency orders remain with authorized "
        "disaster-management officials.</div>",
        unsafe_allow_html=True,
    )
