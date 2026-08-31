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
    """Use certifi's maintained CA bundle for consistent HTTPS verification.

    This keeps certificate verification enabled while avoiding Windows/Python
    installations whose local trust store is incomplete for some public APIs.
    """
    return ssl.create_default_context(cafile=certifi.where())


def demo_envelope(source: str, payload: Any) -> DataEnvelope:
    return DataEnvelope(
        source=source,
        mode="DEMO",
        fetched_at=utc_now_iso(),
        payload=payload,
        stale=False,
    )


def save_envelope(envelope: DataEnvelope, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(envelope), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_cached_envelope(path: str | Path, *, stale: bool = True) -> DataEnvelope:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return DataEnvelope(
        source=data["source"],
        mode="CACHED",
        fetched_at=data["fetched_at"],
        payload=data.get("payload"),
        stale=stale,
        source_url=data.get("source_url"),
        etag=data.get("etag"),
    )


def fetch_json_with_cache(
    *,
    source: str,
    url: str,
    cache_path: str | Path,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> DataEnvelope:
    """Fetch a JSON endpoint with a disk-cache fallback.

    On a successful request the response is returned as LIVE and cached. If the
    request fails and a cache exists, the cached payload is returned as CACHED
    with `stale=True`. If neither live nor cached data is available, the original
    exception is raised so the caller can choose DEMO mode explicitly.
    """
    cache_path = Path(cache_path)
    request = Request(url, headers=headers or {"User-Agent": "SIH26191/1.0"})

    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
            etag = response.headers.get("ETag")
        envelope = DataEnvelope(
            source=source,
            mode="LIVE",
            fetched_at=utc_now_iso(),
            payload=payload,
            stale=False,
            source_url=url,
            etag=etag,
        )
        save_envelope(envelope, cache_path)
        return envelope
    except Exception:
        if cache_path.exists():
            return load_cached_envelope(cache_path, stale=True)
        raise


def fetch_text_with_cache(
    *,
    source: str,
    url: str,
    cache_path: str | Path,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> DataEnvelope:
    """Fetch a UTF-8 text/XML endpoint with the same LIVE/CACHED semantics."""
    cache_path = Path(cache_path)
    request = Request(url, headers=headers or {"User-Agent": "SIH26191/1.0"})

    try:
        with urlopen(request, timeout=timeout, context=_ssl_context()) as response:
            payload = response.read().decode("utf-8")
            etag = response.headers.get("ETag")
        envelope = DataEnvelope(
            source=source,
            mode="LIVE",
            fetched_at=utc_now_iso(),
            payload=payload,
            stale=False,
            source_url=url,
            etag=etag,
        )
        save_envelope(envelope, cache_path)
        return envelope
    except Exception:
        if cache_path.exists():
            return load_cached_envelope(cache_path, stale=True)
        raise


def fetch_text_with_etag_cache(
    *,
    source: str,
    url: str,
    cache_path: str | Path,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
) -> DataEnvelope:
    """Fetch text/XML using ETag revalidation and a disk cache.

    This is intended for feeds such as NDMA SACHET CAP XML whose integration
    guidance requires clients to send the previous ETag and reuse cached XML on
    HTTP 304. A 304 response is returned as CACHED with `stale=False` because the
    server has explicitly confirmed that the cached payload is current.
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
            envelope = DataEnvelope(
                source=source,
                mode="LIVE",
                fetched_at=utc_now_iso(),
                payload=payload,
                stale=False,
                source_url=url,
                etag=response.headers.get("ETag"),
            )
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
