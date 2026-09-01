from scripts.production_gate import run_gate


def test_offline_production_gate_passes():
    result = run_gate()
    assert result["production_ready_offline"] is True
    assert all(check["pass"] for check in result["checks"].values())
