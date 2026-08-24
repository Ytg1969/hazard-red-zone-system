from src.live_data import demo_envelope, validate_mode


def test_demo_envelope_mode():
    env = demo_envelope("unit-test", {"ok": True})
    assert env.mode == "DEMO"
    assert env.payload["ok"] is True


def test_validate_mode():
    assert validate_mode("cached") == "CACHED"
