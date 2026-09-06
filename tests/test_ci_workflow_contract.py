from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FOUNDATION = ROOT / ".github/workflows/tests.yml"
DEPLOYMENT = ROOT / ".github/workflows/deployment-smoke.yml"
FIELD_BUNDLE = ROOT / ".github/workflows/build-field-bundle.yml"


def test_ci_workflows_use_node24_compatible_action_generations():
    foundation = FOUNDATION.read_text(encoding="utf-8")
    deployment = DEPLOYMENT.read_text(encoding="utf-8")
    field_bundle = FIELD_BUNDLE.read_text(encoding="utf-8")
    joined = "\n".join([foundation, deployment, field_bundle])

    assert "actions/checkout@v4" not in joined
    assert joined.count("actions/checkout@v7") == 3
    assert "actions/setup-python@v5" not in joined
    assert deployment.count("actions/setup-python@v7") == 1
    assert field_bundle.count("actions/setup-python@v7") == 1
    assert "conda-incubator/setup-miniconda@v3" not in foundation
    assert "conda-incubator/setup-miniconda@v4.0.1" in foundation
    assert "actions/upload-artifact@v4" not in field_bundle
    assert "actions/upload-artifact@v7" in field_bundle


def test_foundation_miniconda_uses_current_activation_and_channel_inputs():
    text = FOUNDATION.read_text(encoding="utf-8")
    assert "auto-activate-base:" not in text
    assert "auto-activate: false" in text
    assert "conda-remove-defaults: true" in text
    assert "activate-environment: hazard-red-zone" in text
    assert "environment-file: environment.yml" in text
