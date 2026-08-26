from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class DataEnvelope:
    source: str
    mode: str  # LIVE / CACHED / DEMO
    fetched_at: str
    payload: object
    stale: bool = False


def demo_envelope(source: str, payload: object) -> DataEnvelope:
    return DataEnvelope(
        source=source,
        mode="DEMO",
        fetched_at=datetime.now(timezone.utc).isoformat(),
        payload=payload,
        stale=False,
    )


def validate_mode(mode: str) -> str:
    mode = mode.upper()
    if mode not in {"LIVE", "CACHED", "DEMO"}:
        raise ValueError("data mode must be LIVE, CACHED, or DEMO")
    return mode
