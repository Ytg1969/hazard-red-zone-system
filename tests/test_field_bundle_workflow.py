from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/build-field-bundle.yml"
INSTALLER = ROOT / "scripts/windows/INSTALL_OFFLINE.ps1"
LAUNCHER = ROOT / "scripts/windows/START_OFFLINE.cmd"


def test_field_bundle_workflow_contains_offline_contract():
    text = WORKFLOW.read_text(encoding="utf-8")
    required_fragments = [
        "workflow_dispatch:",
        "runs-on: windows-latest",
        "python-version: \"3.12\"",
        "pip download --only-binary=:all:",
        "scripts/cache_road_network.py",
        "scripts/field_preflight.py --strict-road-cache --json",
        "Copy-Item scripts\\windows\\INSTALL_OFFLINE.ps1",
        "Copy-Item scripts\\windows\\START_OFFLINE.cmd",
        "Prove bundle installer works offline",
        "INSTALL_OK.txt",
        "actions/upload-artifact@v4",
        "hazard-command-windows-offline-",
    ]
    for fragment in required_fragments:
        assert fragment in text, f"field bundle workflow is missing required contract: {fragment}"


def test_field_bundle_records_exact_build_provenance():
    text = WORKFLOW.read_text(encoding="utf-8")
    required_fragments = [
        "field-bundle\\BUILD_INFO.txt",
        "repository=${{ github.repository }}",
        "commit_sha=${{ github.sha }}",
        "workflow=${{ github.workflow }}",
        "run_id=${{ github.run_id }}",
        "run_number=${{ github.run_number }}",
        "road_scope=${{ inputs.road_scope }}",
        "built_at_utc=$buildUtc",
        "Keep BUILD_INFO.txt with the bundle",
    ]
    for fragment in required_fragments:
        assert fragment in text, f"field bundle workflow is missing build provenance: {fragment}"


def test_windows_bundle_installer_creates_isolated_offline_environment():
    text = INSTALLER.read_text(encoding="utf-8")
    required_fragments = [
        '"3.12"',
        '"-m", "venv"',
        '"--no-index"',
        '"--find-links"',
        '"scripts\\field_preflight.py"',
        '"--strict-road-cache"',
        '"INSTALL_OK.txt"',
    ]
    for fragment in required_fragments:
        assert fragment in text, f"offline installer is missing required behavior: {fragment}"


def test_windows_bundle_launcher_refuses_unvalidated_environment():
    text = LAUNCHER.read_text(encoding="utf-8")
    required_fragments = [
        ".venv\\Scripts\\python.exe",
        "scripts\\field_preflight.py --strict-road-cache",
        "if errorlevel 1",
        "scripts\\run_offline.py",
    ]
    for fragment in required_fragments:
        assert fragment in text, f"offline launcher is missing required behavior: {fragment}"


def test_pip_runtime_includes_osmnx_for_cached_graph_routing():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    normalized = {line.strip().lower() for line in requirements if line.strip() and not line.startswith("#")}
    assert "osmnx" in normalized
