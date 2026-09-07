from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "pages/14_Evidence_Center.py"


def test_evidence_center_consolidates_secondary_tools():
    text = EVIDENCE.read_text(encoding="utf-8")
    for path in [
        "pages/9_Operational_Data.py",
        "pages/10_GIS_Source_Inspector.py",
        "pages/12_Schema_Mapper.py",
        "pages/11_Calibrated_Hazard_Source.py",
        "pages/8_System_Readiness.py",
        "pages/6_Methodology.py",
        "pages/5_Scenario_Studio.py",
    ]:
        assert path in text
    assert "Uncalibrated live context never changes baseline risk" in text
    assert "Offline field mode" in text
