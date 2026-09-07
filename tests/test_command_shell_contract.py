from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "src" / "ui_theme.py"
APP = ROOT / "app.py"


def test_desktop_shell_uses_command_bar_not_sidebar_as_primary_navigation():
    text = THEME.read_text(encoding="utf-8")
    assert 'st.container(key="hz_topbar")' in text
    assert '"Command", "app.py"' in text
    assert '"Hazard Map", "pages/2_Red_Zone_Map.py"' in text
    assert '"Risk", "pages/3_Risk_Analysis.py"' in text
    assert '"Relocate", "pages/4_Relocation_Planner.py"' in text
    assert '"Briefing", "pages/13_Briefing.py"' in text
    assert "CONTROL DRAWER" in text
    assert "Evidence & boundaries" in text
    assert "Data & configuration" in text
    assert "position:sticky" in text


def test_command_home_carries_operator_focus_and_decision_gates():
    text = APP.read_text(encoding="utf-8")
    assert 'st.session_state["focus_location"]' in text
    assert 'render_section_header(' in text
    assert '"Decision board"' in text
    assert 'render_decision_gate(' in text
    assert '"Analytical risk available"' in text
    assert '"Capacity check"' in text
    assert '"Authority boundary"' in text
    assert '"Decision support only; the application does not issue evacuation orders."' in text
