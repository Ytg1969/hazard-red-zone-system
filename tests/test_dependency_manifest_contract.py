from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
ROUTING_REQUIREMENTS = ROOT / "requirements-routing.txt"
DEV_REQUIREMENTS = ROOT / "requirements-dev.txt"
ENVIRONMENT = ROOT / "environment.yml"

EXPECTED_DIRECT = {
    "streamlit": "1.63.0",
    "pandas": "3.0.5",
    "numpy": "2.5.2",
    "geopandas": "1.1.4",
    "shapely": "2.1.2",
    "folium": "0.20.0",
    "streamlit-folium": "0.27.4",
    "plotly": "6.9.0",
    "networkx": "3.6.1",
    "osmnx": "2.1.1",
    "reportlab": "5.0.1",
    "certifi": "2026.7.22",
    "openpyxl": "3.1.5",
}


def _pip_pins() -> dict[str, str]:
    pins = {}
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        pins[name.lower()] = version
    return pins


def _active_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def test_production_requirements_are_exactly_pinned():
    assert _pip_pins() == EXPECTED_DIRECT


def test_conda_manifest_matches_direct_production_versions():
    text = ENVIRONMENT.read_text(encoding="utf-8")
    for name, version in EXPECTED_DIRECT.items():
        if name == "streamlit-folium":
            assert f"- {name}=={version}" in text
        else:
            assert f"- {name}={version}" in text

    assert "- python=3.12" in text
    assert "- pytest=9.1.1" in text
    assert "scikit-learn" not in text


def test_no_unpinned_direct_dependencies_remain():
    requirements_text = REQUIREMENTS.read_text(encoding="utf-8")
    assert all("==" in line for line in requirements_text.splitlines() if line.strip() and not line.startswith("#"))


def test_routing_profile_is_only_a_production_alias():
    assert _active_lines(ROUTING_REQUIREMENTS) == ["-r requirements.txt"]


def test_dev_profile_uses_production_pins_and_pinned_pytest():
    assert _active_lines(DEV_REQUIREMENTS) == ["-r requirements.txt", "pytest==9.1.1"]
