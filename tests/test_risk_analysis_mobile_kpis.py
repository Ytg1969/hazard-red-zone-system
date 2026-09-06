from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RISK_ANALYSIS = ROOT / "pages/3_Risk_Analysis.py"


def test_risk_analysis_decision_metrics_use_shared_responsive_kpis():
    text = RISK_ANALYSIS.read_text(encoding="utf-8")
    assert "render_kpi_strip" in text
    assert '("Risk Score",' in text
    assert '("Hazard Score",' in text
    assert '("Vulnerable Population",' in text
    assert '("Relocation Priority",' in text
    assert 'st.metric("Risk Score"' not in text
    assert 'st.metric("Hazard Score"' not in text
    assert 'st.metric("Vulnerable Population"' not in text
    assert 'st.metric("Relocation Priority"' not in text
