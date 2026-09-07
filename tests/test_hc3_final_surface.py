from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
VERIFIER = ROOT / ".github" / "workflows" / "streamlit-site-verification.yml"


def test_hc3_final_surface_has_single_command_entrypoint():
    assert APP.exists()
    assert not (ROOT / "pages/0_Operations_Hub.py").exists()
    assert not (ROOT / "pages/1_Command_Center.py").exists()


def test_hc3_final_release_identity_and_routes_are_consistent():
    app = APP.read_text(encoding="utf-8")
    verifier = VERIFIER.read_text(encoding="utf-8")
    assert 'DEPLOYMENT_RELEASE = "HC3-2026-09-07-r2"' in app
    assert "EXPECTED_RELEASE: HC3-2026-09-07-r2" in verifier
    for route in ["/Red_Zone_Map", "/Risk_Analysis", "/Relocation_Planner", "/Briefing", "/Evidence_Center", "/About_System"]:
        assert route in verifier
