from io import BytesIO

from src import live_data


class _Headers:
    def get(self, key, default=None):
        return "etag-1" if key == "ETag" else default


class _Response:
    headers = _Headers()

    def __init__(self, payload: bytes):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.payload


def test_binary_fetch_is_cached_and_reused_on_refresh_failure(monkeypatch, tmp_path):
    payload = b"PK\x03\x04binary-xlsx-test"
    monkeypatch.setattr(live_data, "urlopen", lambda *args, **kwargs: _Response(payload))
    cache_path = tmp_path / "authority.xlsx.bin"

    live = live_data.fetch_bytes_with_cache(
        source="Authority XLSX", url="https://example.test/data.xlsx", cache_path=cache_path
    )
    assert live.mode == "LIVE"
    assert live.payload == payload
    assert live.stale is False
    assert cache_path.read_bytes() == payload

    def fail(*args, **kwargs):
        raise OSError("network down")

    monkeypatch.setattr(live_data, "urlopen", fail)
    cached = live_data.fetch_bytes_with_cache(
        source="Authority XLSX", url="https://example.test/data.xlsx", cache_path=cache_path
    )
    assert cached.mode == "CACHED"
    assert cached.payload == payload
    assert cached.stale is True
    assert cached.source_url == "https://example.test/data.xlsx"
