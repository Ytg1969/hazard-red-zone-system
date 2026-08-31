from src.live_data import (
    demo_envelope,
    fetch_text_with_etag_cache,
    load_cached_envelope,
    save_envelope,
    validate_mode,
)


def test_demo_envelope_mode():
    env = demo_envelope("unit-test", {"ok": True})
    assert env.mode == "DEMO"
    assert env.payload["ok"] is True


def test_validate_mode():
    assert validate_mode("cached") == "CACHED"


def test_cached_envelope_round_trip(tmp_path):
    cache_file = tmp_path / "cache.json"
    original = demo_envelope("unit-test", {"value": 42})
    original.mode = "LIVE"
    original.source_url = "https://example.invalid/data"
    original.etag = '"abc123"'
    save_envelope(original, cache_file)

    cached = load_cached_envelope(cache_file)
    assert cached.mode == "CACHED"
    assert cached.stale is True
    assert cached.payload["value"] == 42
    assert cached.source_url == "https://example.invalid/data"
    assert cached.etag == '"abc123"'


def test_etag_fetcher_is_exposed():
    assert callable(fetch_text_with_etag_cache)
