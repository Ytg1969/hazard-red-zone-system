from src.runtime_mode import offline_mode, runtime_mode_label
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


def test_offline_mode_defaults_to_connected(monkeypatch):
    monkeypatch.delenv("SIH_OFFLINE_MODE", raising=False)
    assert offline_mode() is False
    assert runtime_mode_label() == "CONNECTED"


def test_offline_mode_accepts_explicit_true_values(monkeypatch):
    for value in ["1", "true", "YES", "on", "enabled"]:
        monkeypatch.setenv("SIH_OFFLINE_MODE", value)
        assert offline_mode() is True
        assert runtime_mode_label() == "OFFLINE"


def test_offline_mode_rejects_false_values(monkeypatch):
    for value in ["0", "false", "no", "", "connected"]:
        monkeypatch.setenv("SIH_OFFLINE_MODE", value)
        assert offline_mode() is False
