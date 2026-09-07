from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
BRIEFING = ROOT / "pages/13_Briefing.py"
REDESIGN_DOC = ROOT / "docs/UI_REDESIGN.md"


def test_command_home_preserves_core_safety_contracts():
    text = APP.read_text(encoding="utf-8")
    assert "available_shelter_capacity" in text
    assert "immediate_relocation_population" in text
    assert "Capacity gap" in text
    assert "pages/2_Red_Zone_Map.py" in text
    assert "pages/3_Risk_Analysis.py" in text
    assert "pages/4_Relocation_Planner.py" in text


def test_incident_briefing_exports_safety_contract():
    text = BRIEFING.read_text(encoding="utf-8")
    assert '"risk_equation": "Risk = 0.35H + 0.25E + 0.25V + 0.15A"' in text
    assert '"external_context_mutates_baseline_risk": False' in text
    assert '"shelter_capacity_is_hard_constraint": True' in text
    assert '"automated_evacuation_order": False' in text
    assert "Download briefing JSON" in text
    assert "Download priority CSV" in text


def test_redesign_document_keeps_offline_and_provenance_first_class():
    text = REDESIGN_DOC.read_text(encoding="utf-8")
    assert "LIVE/CACHED/DEMO" in text
    assert "Offline mode must remain a first-class usable path" in text
    assert "Never overbook shelter capacity" in text
    assert "Never present an automated evacuation order" in text
