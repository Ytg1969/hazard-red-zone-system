from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RED_ZONE = ROOT / "pages/2_Red_Zone_Map.py"
RELOCATION = ROOT / "pages/4_Relocation_Planner.py"


def test_red_zone_summary_uses_shared_responsive_kpis():
    text = RED_ZONE.read_text(encoding="utf-8")
    assert "render_kpi_strip" in text
    assert '("Safe candidates", len(ranked_shelters)' in text
    assert "summary = st.columns(4)" not in text


def test_relocation_decision_metrics_use_shared_responsive_kpis():
    text = RELOCATION.read_text(encoding="utf-8")
    assert "render_kpi_strip" in text
    assert 'recommendation_metrics = [' in text
    assert '("Remaining Deficit",' in text
    assert '("Batch Deficit",' in text
    assert "primary_metrics = st.columns(2)" not in text
    assert "a1, a2, a3 = st.columns(3)" not in text
    assert "b1, b2, b3 = st.columns(3)" not in text
    assert "o1, o2, o3 = st.columns(3)" not in text
