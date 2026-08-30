from scripts.demo_gate import run_demo_gate


def test_demo_gate_reports_ready():
    result = run_demo_gate()
    assert result["demo_ready"] is True
    assert result["data_mode"] == "DEMO"
    assert result["habitations"] > 0
    assert result["shelters"] > 0
    assert result["available_shelter_capacity"] >= 0
