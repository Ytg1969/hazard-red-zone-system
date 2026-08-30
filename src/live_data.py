from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


VALID_MODES = {"LIVE", "CACHED", "DEMO"}


@dataclass
class DataEnvelope:
    source: str
    mode: str  # LIVE / CACHED / DEMO
    fetched_at: str
    payload: Any
    stale: bool = False
    source_url: str | None = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_mode(mode: str) -> str:
    mode = str(mode).upper()
    if mode not in VALID_MODES:
        raise ValueError("data mode must be LIVE, CACHED, or DEMO")
    return mode


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
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        envelope = DataEnvelope(
            source=source,
            mode="LIVE",
            fetched_at=utc_now_iso(),
            payload=payload,
            stale=False,
            source_url=url,
        )
        save_envelope(envelope, cache_path)
        return envelope
    except Exception:
        if cache_path.exists():
            return load_cached_envelope(cache_path, stale=True)
        raise
