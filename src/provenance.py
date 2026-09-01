"""Data provenance and freshness helpers for production-facing operational views."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

VALID_MODES = {"LIVE", "CACHED", "DEMO"}


def normalize_mode(value: Any) -> str:
    mode = str(value or "DEMO").upper().strip()
    return mode if mode in VALID_MODES else "DEMO"


def parse_timestamp(value: Any) -> datetime | None:
    if value in (None, "", "—"):
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def freshness_status(
    fetched_at: Any,
    *,
    now: datetime | None = None,
    fresh_minutes: int = 30,
    stale_minutes: int = 180,
) -> dict[str, Any]:
    """Return deterministic freshness metadata without pretending missing time is fresh."""
    parsed = parse_timestamp(fetched_at)
    if parsed is None:
        return {"status": "UNKNOWN", "age_minutes": None, "fetched_at": None}

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = max(0.0, (current.astimezone(timezone.utc) - parsed).total_seconds() / 60.0)

    if age <= fresh_minutes:
        status = "FRESH"
    elif age <= stale_minutes:
        status = "AGING"
    else:
        status = "STALE"
    return {"status": status, "age_minutes": round(age, 1), "fetched_at": parsed.isoformat()}


def source_health(source: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Normalize adapter results into a stable source-health contract."""
    mode = normalize_mode(source.get("mode"))
    fetched_at = source.get("fetched_at") or source.get("retrieved_at") or source.get("timestamp")
    freshness = freshness_status(fetched_at, now=now)
    error = source.get("error")
    stale_flag = bool(source.get("stale", False))

    if error:
        operational_state = "DEGRADED"
    elif mode == "DEMO":
        operational_state = "DEMO_ONLY"
    elif stale_flag or freshness["status"] == "STALE":
        operational_state = "STALE"
    elif freshness["status"] == "UNKNOWN":
        operational_state = "AVAILABLE_UNTIMED"
    else:
        operational_state = "HEALTHY"

    return {
        "mode": mode,
        "operational_state": operational_state,
        "freshness": freshness["status"],
        "age_minutes": freshness["age_minutes"],
        "fetched_at": freshness["fetched_at"],
        "stale": stale_flag,
        "error": str(error) if error else None,
        "source": source.get("source") or source.get("name") or "Unknown source",
        "access_status": source.get("access_status"),
    }


def provenance_record(
    *,
    dataset: str,
    source: str,
    mode: str,
    role: str,
    affects_risk: bool,
    notes: str = "",
) -> dict[str, Any]:
    """Create an auditable provenance row used by exports and readiness views."""
    return {
        "dataset": dataset,
        "source": source,
        "mode": normalize_mode(mode),
        "role": role,
        "affects_risk": bool(affects_risk),
        "notes": notes,
    }


def default_provenance_register() -> list[dict[str, Any]]:
    """Known source roles for the current SIH26191 implementation."""
    return [
        provenance_record(dataset="Demo habitations", source="Bundled CSV", mode="DEMO", role="Analytical input", affects_risk=True, notes="Synthetic operational values on real geography."),
        provenance_record(dataset="Demo shelters", source="Bundled CSV", mode="DEMO", role="Capacity and relocation input", affects_risk=False, notes="Synthetic capacities and occupancy."),
        provenance_record(dataset="Demo hazard geometry", source="Bundled GeoJSON", mode="DEMO", role="GIS exposure context", affects_risk=True, notes="Synthetic analytical footprints."),
        provenance_record(dataset="Weather", source="Open-Meteo", mode="LIVE", role="Situational context", affects_risk=False, notes="Context only until calibrated."),
        provenance_record(dataset="Air quality", source="Open-Meteo Air Quality", mode="LIVE", role="Situational context", affects_risk=False, notes="Context only until calibrated."),
        provenance_record(dataset="Earthquakes", source="USGS FDSN", mode="LIVE", role="Situational context", affects_risk=False, notes="Context only until calibrated."),
        provenance_record(dataset="Disaster events", source="GDACS", mode="LIVE", role="Situational context", affects_risk=False, notes="Context only until calibrated."),
        provenance_record(dataset="Natural events", source="NASA EONET", mode="LIVE", role="Situational context", affects_risk=False, notes="Context only until calibrated."),
        provenance_record(dataset="District warnings/rainfall", source="IMD", mode="LIVE", role="Official context", affects_risk=False, notes="Authorization may be required."),
        provenance_record(dataset="National alerts", source="NDMA SACHET", mode="LIVE", role="Official alert context", affects_risk=False, notes="LIVE only when a verified feed is configured."),
        provenance_record(dataset="Hazard overlays", source="NRSC/ISRO Bhuvan WMS", mode="LIVE", role="Authoritative/historical GIS context", affects_risk=False, notes="No numeric risk mutation before layer calibration."),
        provenance_record(dataset="Road routing", source="OSM / OSRM", mode="LIVE", role="Route evidence", affects_risk=False, notes="No live-traffic or hazard-avoidance claim."),
    ]
