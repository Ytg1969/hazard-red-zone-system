from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
CONTRACT = ROOT / "docs" / "streamlit_auto_update.md"
PRODUCTION_GUIDE = ROOT / "docs" / "production_deployment.md"
VERIFIER = ROOT / ".github" / "workflows" / "streamlit-site-verification.yml"
PUBLIC_APP_URL = "https://hazard-red-zone-system-qmi7oeaai7ewky3bfmrnpr.streamlit.app"
EXPECTED_RELEASE = "HC3-2026-09-07-r1"


def test_public_streamlit_coordinates_are_pinned_to_main_app():
    contract = CONTRACT.read_text(encoding="utf-8")
    guide = PRODUCTION_GUIDE.read_text(encoding="utf-8")

    required = [
        "Ytg1969/hazard-red-zone-system",
        "branch: `main`",
        "entrypoint: `app.py`",
        "Python baseline: `3.12`",
    ]
    for fragment in required:
        assert fragment in contract

    assert "- branch: `main`" in guide
    assert "- entrypoint: `app.py`" in guide


def test_streamlit_contract_requires_host_driven_auto_update_and_release_gates():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "Community Cloud automatically refreshes the deployed application" in text
    assert "No separate GitHub Actions deployment webhook is required" in text
    assert "Foundation Tests and Deployment Smoke" in text
    assert "feature branches and unreviewed experimental branches must never be configured" in text
    assert "environment.yml" in text
    assert PUBLIC_APP_URL in text


def test_post_merge_streamlit_verifier_is_main_only_and_browser_aware():
    workflow = VERIFIER.read_text(encoding="utf-8")

    assert "name: Streamlit Site Verification" in workflow
    assert 'workflows: ["Deployment Smoke"]' in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert f"STREAMLIT_APP_URL: {PUBLIC_APP_URL}" in workflow
    assert "for attempt in $(seq 1 60)" in workflow
    assert "playwright" in workflow.lower()
    assert "ModuleNotFoundError" in workflow
    assert "ImportError" in workflow
    assert "Traceback:" in workflow
    assert "share.streamlit.io/-/auth" in workflow
    assert "page.url" in workflow


def test_public_verifier_covers_hazard_command_2_pages():
    workflow = VERIFIER.read_text(encoding="utf-8")
    required_routes = [
        '("briefing", "/Briefing")',
        '("evidence-center", "/Evidence_Center")',
        '("system-boundaries", "/About_System")',
    ]
    for route in required_routes:
        assert route in workflow


def test_public_verifier_rejects_unknown_page_redirects_and_waits_for_release_routes():
    workflow = VERIFIER.read_text(encoding="utf-8")
    assert "from urllib.parse import urlsplit" in workflow
    assert "release_routes = [" in workflow
    assert "for attempt in range(1, 26):" in workflow
    assert "page.wait_for_timeout(6000)" in workflow
    assert "final_path != expected_path" in workflow
    assert "resolved to {final_path} instead of expected route {expected_path}" in workflow
    assert "Public Streamlit deployment did not register the expected release" in workflow


def test_public_verifier_proves_exact_main_app_release_marker():
    app = APP.read_text(encoding="utf-8")
    workflow = VERIFIER.read_text(encoding="utf-8")

    assert f'DEPLOYMENT_RELEASE = "{EXPECTED_RELEASE}"' in app
    assert 'st.caption(f"Release {DEPLOYMENT_RELEASE}")' in app
    assert f"EXPECTED_RELEASE: {EXPECTED_RELEASE}" in workflow
    assert 'expected_release = os.environ["EXPECTED_RELEASE"]' in workflow
    assert 'release_text = f"Release {expected_release}"' in workflow
    assert "release_text not in home_body" in workflow
    assert 'label == "home" and release_text not in body' in workflow


def test_auto_update_contract_does_not_weaken_analytical_safety():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "LIVE external context remains additive unless calibrated" in text
    assert "unknown values remain unknown" in text
    assert "shelter capacity remains a hard constraint" in text
    assert "Risk = 0.35H + 0.25E + 0.25V + 0.15A" in text
