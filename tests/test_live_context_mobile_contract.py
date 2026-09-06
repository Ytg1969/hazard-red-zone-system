from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages/7_Live_Data_Context.py"


def test_live_context_uses_shared_responsive_kpi_grid():
    text = PAGE.read_text(encoding="utf-8")
    assert "render_kpi_strip" in text
    assert '("Temperature",' in text
    assert '("Nearby Events",' in text
    assert '("Current / cached",' in text
    assert '("Offline-disabled",' in text
    assert '("Needs attention",' in text
    assert "metrics = st.columns(6" not in text
    assert "status_cols = st.columns(3" not in text
