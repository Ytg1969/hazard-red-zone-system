from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


PAGES = [
    Path("app.py"),
    Path("pages/1_Command_Center.py"),
    Path("pages/2_Red_Zone_Map.py"),
    Path("pages/3_Risk_Analysis.py"),
    Path("pages/4_Relocation_Planner.py"),
    Path("pages/5_Scenario_Studio.py"),
    Path("pages/6_Methodology.py"),
]


@pytest.mark.parametrize("path", PAGES, ids=lambda path: path.name)
def test_streamlit_page_smoke(path: Path):
    app = AppTest.from_file(str(path), default_timeout=20)
    app.run()
    assert not app.exception, f"Streamlit page raised exception: {path}"
