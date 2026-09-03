from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import ssl
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import certifi


VALID_MODES = {"LIVE", "CACHED", "DEMO"}


@dataclass
class DataEnvelope:
    source: str
    mode: str  # LIVE / CACHED / DEMO
    fetched_at: str
    payload: Any
    stale: bool = False
    source_url: str | None = None
    etag: str | None = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_mode(mode: str) -> str:
    mode = str(mode).upper()
    if mode not in VALID_MODES:
        raise ValueError("data mode must be LIVE, CACHED, or DEMO")
    return mode


def _ssl_context() -> ssl.SSLContext:
    """Use certifi's maintained CA bundle for consistent HTTPS verification."""
    return ssl.create_default_context(cafile=certifi.where())


def demo_envelope(source: str, payload: Any) -> DataEnvelope:
    return DataEnvelope(source=source, mode="DEMO", fetched_at=utc_now_iso(), payload=payload, stale=False)


def save_envelope(envelope: DataEnvelope, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(envelope), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_cached_envelope(path: str | Path, *, stale: bool = True) -> DataEnvelope:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return DataEnvelope(
        source=data["source"], mode="CACHED", fetched_at=data["fetched_at"], payload=data.get("payload"),
        stale=stale, source_url=data.get("source_url"), etag=data.get("etag"),
    )


def _binary_meta_path(cache_path: Path) -> Path:
    return cache_path.with_name(cache_path.name + ".meta.json")


def _save_binary_envelope(envelope: DataEnvelope, cache_path: Path) -> None:
    if not isinstance(envelope.payload, (bytes, bytearray)):
        raise TypeError("binary cache payload must be bytes")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(bytes(envelope.payload))
    meta = {
        "source": envelope.source,
        "fetched_at": envelope.fetched_at,
        "source_url": envelope.source_url,
        "etag": envelope.etag,
    }
    _binary_meta_path(cache_path).write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_binary_envelope(cache_path: Path, *, stale: bool = True) -> DataEnvelope:
    meta_path = _binary_meta_path(cache_path)
    if not cache_path.exists() or not meta_path.exists():
        raise FileNotFoundError("binary cache is incomplete")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    return DataEnvelope(
        source=meta["source"], mode="CACHED", fetched_at=meta["fetched_at"], payload=cache_path.read_bytes(),
        stale=stale, source_url=meta.get("source_url"), etag=meta.get("etag"),
    )


def fetch_json_with_cache(*, source: str, url: str, cache_path: str | Path, headers: dict[str, str] | None = None, timeout: float = 10.0) -> DataEnvelope:
    """Fetch a JSON endpoint with a disk-cache fallback."""
    cache_path = Path(cache_path)
    request = Request(url, headers=headers or {"User-Agent": "SIH26191/1.0"})
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
            etag = response.headers.get("ETag")
        envelope = DataEnvelope(source=source, mode="LIVE", fetched_at=utc_now_iso(), payload=payload, stale=False, source_url=url, etag=etag)
        save_envelope(envelope, cache_path)
        return envelope
    except Exception:
        if cache_path.exists():
            return load_cached_envelope(cache_path, stale=True)
        raise


def fetch_text_with_cache(*, source: str, url: str, cache_path: str | Path, headers: dict[str, str] | None = None, timeout: float = 10.0) -> DataEnvelope:
    """Fetch a UTF-8 text/XML endpoint with LIVE/CACHED semantics."""
    cache_path = Path(cache_path)
    request = Request(url, headers=headers or {"User-Agent": "SIH26191/1.0"})
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = response.read().decode("utf-8")
            etag = response.headers.get("ETag")
        envelope = DataEnvelope(source=source, mode="LIVE", fetched_at=utc_now_iso(), payload=payload, stale=False, source_url=url, etag=etag)
        save_envelope(envelope, cache_path)
        return envelope
    except Exception:
        if cache_path.exists():
            return load_cached_envelope(cache_path, stale=True)
        raise


def fetch_bytes_with_cache(*, source: str, url: str, cache_path: str | Path, headers: dict[str, str] | None = None, timeout: float = 10.0) -> DataEnvelope:
    """Fetch binary content with the same explicit LIVE/CACHED semantics.

    Binary payload and metadata are stored separately so XLSX and other approved
    binary authority downloads are never JSON-encoded or silently decoded as
    text. A failed refresh may reuse a complete prior binary cache as stale.
    """
    cache_path = Path(cache_path)
    request = Request(url, headers=headers or {"User-Agent": "SIH26191/1.0"})
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = response.read()
            etag = response.headers.get("ETag")
        envelope = DataEnvelope(source=source, mode="LIVE", fetched_at=utc_now_iso(), payload=payload, stale=False, source_url=url, etag=etag)
        _save_binary_envelope(envelope, cache_path)
        return envelope
    except Exception:
        if cache_path.exists() and _binary_meta_path(cache_path).exists():
            return _load_binary_envelope(cache_path, stale=True)
        raise


def fetch_text_with_etag_cache(*, source: str, url: str, cache_path: str | Path, headers: dict[str, str] | None = None, timeout: float = 10.0) -> DataEnvelope:
    """Fetch text/XML using ETag revalidation and a disk cache.

    Intended for feeds such as NDMA SACHET CAP XML. HTTP 304 reuses the cached
    payload as CACHED with stale=False because the server confirmed it is current.
    """
    cache_path = Path(cache_path)
    request_headers = {"User-Agent": "SIH26191/1.0"}
    if headers:
        request_headers.update(headers)

    cached: DataEnvelope | None = None
    if cache_path.exists():
        try:
            cached = load_cached_envelope(cache_path, stale=False)
        except Exception:
            cached = None
    if cached and cached.etag:
        request_headers["If-None-Match"] = cached.etag

    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = response.read().decode("utf-8")
            envelope = DataEnvelope(source=source, mode="LIVE", fetched_at=utc_now_iso(), payload=payload, stale=False, source_url=url, etag=response.headers.get("ETag"))
        save_envelope(envelope, cache_path)
        return envelope
    except HTTPError as exc:
        if exc.code == 304 and cached is not None:
            cached.mode = "CACHED"
            cached.stale = False
            return cached
        if cache_path.exists():
            return load_cached_envelope(cache_path, stale=True)
        raise
    except Exception:
        if cache_path.exists():
            return load_cached_envelope(cache_path, stale=True)
        raise
