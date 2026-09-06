from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/build-field-bundle.yml"


def test_field_bundle_workflow_contains_offline_contract():
    text = WORKFLOW.read_text(encoding="utf-8")
    required_fragments = [
        "workflow_dispatch:",
        "runs-on: windows-latest",
        "python-version: \"3.12\"",
        "pip download --only-binary=:all:",
        "scripts/cache_road_network.py",
        "scripts/field_preflight.py --strict-road-cache --json",
        "actions/upload-artifact@v4",
        "hazard-command-windows-offline-",
    ]
    for fragment in required_fragments:
        assert fragment in text, f"field bundle workflow is missing required contract: {fragment}"


def test_pip_runtime_includes_osmnx_for_cached_graph_routing():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    normalized = {line.strip().lower() for line in requirements if line.strip() and not line.startswith("#")}
    assert "osmnx" in normalized
