from src.streamlit_workspace import operational_data_required


def test_operational_data_required_defaults_false(monkeypatch):
    monkeypatch.delenv("SIH_REQUIRE_OPERATIONAL_DATA", raising=False)
    assert operational_data_required() is False


def test_operational_data_required_accepts_true_values(monkeypatch):
    for value in ["true", "1", "yes", "required", "production"]:
        monkeypatch.setenv("SIH_REQUIRE_OPERATIONAL_DATA", value)
        assert operational_data_required() is True


def test_operational_data_required_rejects_false_values(monkeypatch):
    for value in ["false", "0", "no", ""]:
        monkeypatch.setenv("SIH_REQUIRE_OPERATIONAL_DATA", value)
        assert operational_data_required() is False
