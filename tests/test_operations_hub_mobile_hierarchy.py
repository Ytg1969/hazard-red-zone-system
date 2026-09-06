from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "pages/0_Operations_Hub.py"


def test_operations_hub_compacts_decision_and_live_metrics():
    text = PAGE.read_text(encoding="utf-8")
    assert 'render_kpi_strip([' in text
    assert '("Highest Risk",' in text
    assert '("Safe Inventory",' in text
    assert '("Usable Sources",' in text
    assert '("Nearby Events",' in text
    assert "status_cols = st.columns(7" not in text
    assert "live_metrics = st.columns(6" not in text


def test_operations_hub_progressively_discloses_secondary_workflows():
    text = PAGE.read_text(encoding="utf-8")
    assert 'with st.expander("Source context controls", expanded=False):' in text
    assert 'with st.expander("Per-source status", expanded=False):' in text
    assert 'with st.expander("Operator workflow · 5 steps", expanded=False):' in text
    assert '.head(10)' in text
    assert 'with st.expander(f"Full priority register · {len(priority_rows)} records", expanded=False):' in text
