from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "app.py"
CHILD_PAGES = [
    "pages/0_Operations_Hub.py",
    "pages/1_Command_Center.py",
    "pages/2_Red_Zone_Map.py",
    "pages/3_Risk_Analysis.py",
    "pages/4_Relocation_Planner.py",
    "pages/5_Scenario_Studio.py",
    "pages/6_Methodology.py",
    "pages/7_Live_Data_Context.py",
    "pages/8_System_Readiness.py",
    "pages/9_Operational_Data.py",
    "pages/10_GIS_Source_Inspector.py",
    "pages/11_Calibrated_Hazard_Source.py",
    "pages/12_Schema_Mapper.py",
]
STRICT_MODE_PAGES = [
    "pages/0_Operations_Hub.py",
    "pages/1_Command_Center.py",
    "pages/2_Red_Zone_Map.py",
    "pages/3_Risk_Analysis.py",
    "pages/4_Relocation_Planner.py",
    "pages/5_Scenario_Studio.py",
    "pages/7_Live_Data_Context.py",
    "pages/8_System_Readiness.py",
    "pages/9_Operational_Data.py",
    "pages/12_Schema_Mapper.py",
]


def _main_app() -> AppTest:
    app = AppTest.from_file(MAIN, default_timeout=30)
    app.run()
    assert not app.exception, f"Main Streamlit app raised exception: {app.exception}"
    return app


def test_streamlit_main_smoke():
    _main_app()


@pytest.mark.parametrize("page", CHILD_PAGES, ids=lambda page: Path(page).name)
def test_streamlit_child_page_smoke(page: str):
    path = ROOT / page
    assert path.exists(), f"Streamlit page is missing: {path}"
    app = _main_app()
    app.switch_page(page).run()
    assert not app.exception, f"Streamlit child page raised exception: {page}: {app.exception}"


def test_streamlit_main_strict_production_mode_without_feeds(monkeypatch):
    """Strict mode must fail closed in the UI, not crash or fall back to DEMO."""
    monkeypatch.setenv("SIH_REQUIRE_OPERATIONAL_DATA", "true")
    monkeypatch.delenv("SIH_HABITATION_CSV_URL", raising=False)
    monkeypatch.delenv("SIH_SHELTER_CSV_URL", raising=False)
    app = _main_app()
    assert not app.exception


@pytest.mark.parametrize("page", STRICT_MODE_PAGES, ids=lambda page: f"strict-{Path(page).name}")
def test_streamlit_pages_survive_strict_mode_without_feeds(page: str, monkeypatch):
    """Every operator-facing page must remain recoverable when production feeds are absent."""
    monkeypatch.setenv("SIH_REQUIRE_OPERATIONAL_DATA", "true")
    monkeypatch.delenv("SIH_HABITATION_CSV_URL", raising=False)
    monkeypatch.delenv("SIH_SHELTER_CSV_URL", raising=False)
    app = _main_app()
    app.switch_page(page).run()
    assert not app.exception, f"Strict-mode page raised exception: {page}: {app.exception}"
