from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_SACHET_RSS = "https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml"
WMO_NDMA_REGISTER = "https://alertingauthority.wmo.int/authorities.php?recId=331"


def test_operator_docs_use_supported_python_312():
    paths = [
        ROOT / "README.md",
        ROOT / "DEPLOYMENT.md",
        ROOT / "docs" / "best_of_both_merge.md",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert "py -3.13" not in combined
    assert "py -3.12" in combined


def test_verified_sachet_feed_is_documented_without_placeholder():
    paths = [
        ROOT / "README.md",
        ROOT / "DEPLOYMENT.md",
        ROOT / "docs" / "production_deployment.md",
        ROOT / "docs" / "streamlit_secrets.example.toml",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)
    assert OFFICIAL_SACHET_RSS in combined
    assert WMO_NDMA_REGISTER in combined
    assert "https://sachet.ndma.gov.in/...verified-feed..." not in combined


def test_production_guide_matches_current_osmnx_manifest():
    guide = (ROOT / "docs" / "production_deployment.md").read_text(encoding="utf-8")
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "osmnx==2.1.1" in requirements
    assert "including OSMnx for cached local GraphML routing" in guide
    assert "excludes test tooling and the optional OSMnx" not in guide
