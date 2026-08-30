from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]

PAGES = [
    ROOT / "app.py",
    ROOT / "pages/1_Command_Center.py",
    ROOT / "pages/2_Red_Zone_Map.py",
    ROOT / "pages/3_Risk_Analysis.py",
    ROOT / "pages/4_Relocation_Planner.py",
    ROOT / "pages/5_Scenario_Studio.py",
    ROOT / "pages/6_Methodology.py",
]


@pytest.mark.parametrize("path", PAGES, ids=lambda path: path.name)
def test_streamlit_page_smoke(path: Path):
    app = AppTest.from_file(path, default_timeout=20)
    app.run()
    assert not app.exception, f"Streamlit page raised exception: {path}"
