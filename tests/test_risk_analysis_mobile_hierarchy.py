from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages/3_Risk_Analysis.py"


def test_risk_analysis_uses_compact_decision_first_hierarchy():
    text = PAGE.read_text(encoding="utf-8")
    assert "render_kpi_strip" in text
    assert '("Risk",' in text
    assert '("Top driver",' in text
    assert '("Vulnerable",' in text
    assert 'st.markdown("## Why this location is at risk")' in text
    assert 'with st.expander("Hazard evidence & calibration", expanded=False):' in text
    assert 'with st.expander("Exact risk calculation", expanded=False):' in text

    explanation = text.index('st.markdown("## Why this location is at risk")')
    hazard_detail = text.index('with st.expander("Hazard evidence & calibration"')
    assert explanation < hazard_detail


def test_risk_analysis_preserves_model_and_mobile_auto_state():
    text = PAGE.read_text(encoding="utf-8")
    assert 'initial_sidebar_state="auto"' in text
    assert "Risk = 0.35H + 0.25E + 0.25V + 0.15A" in text
    assert 'st.page_link("pages/4_Relocation_Planner.py"' in text
