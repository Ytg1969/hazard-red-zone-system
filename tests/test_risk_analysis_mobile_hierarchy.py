from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages/3_Risk_Analysis.py"


def test_risk_analysis_uses_compact_summary_and_decision_first_order():
    text = PAGE.read_text(encoding="utf-8")
    assert "render_kpi_strip" in text
    assert '("Risk Score",' in text
    assert '("Vulnerable Population",' in text
    assert "st.metric(\"Risk Score\"" not in text
    assert 'with st.expander("Hazard evidence and calibration detail", expanded=False):' in text
    assert 'with st.expander("Final risk-factor detail", expanded=False):' in text

    explanation = text.index('st.subheader("Why this location is classified this way")')
    hazard_detail = text.index('with st.expander("Hazard evidence and calibration detail"')
    assert explanation < hazard_detail


def test_risk_analysis_sidebar_is_mobile_auto_state():
    text = PAGE.read_text(encoding="utf-8")
    assert 'initial_sidebar_state="auto"' in text
