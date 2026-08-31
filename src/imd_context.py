"""Official IMD weather-warning/rainfall context for the three-city demo.

The adapter uses endpoints documented by the India Meteorological Department.
It is intentionally contextual: LIVE/CACHED IMD observations and warnings do
not silently alter the deterministic risk score. Production calibration must
map verified source fields into the analytical model explicitly.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from src.live_data import fetch_json_with_cache

IMD_WARNING_URL = "https://mausam.imd.gov.in/api/warnings_district_api.php"
IMD_RAINFALL_URL = "https://mausam.imd.gov.in/api/districtwise_rainfall_api.php"

CITY_DISTRICT_ALIASES = {
    "Puri": {"puri"},
    "Guwahati": {"kamrup metropolitan", "kamrup metro", "kamrup(m)", "kamrup (m)", "guwahati"},
    "Chennai": {"chennai"},
}

WARNING_CODES = {
    "1": "No Warning",
    "2": "Heavy Rain",
    "3": "Heavy Snow",
    "4": "Thunderstorm / Lightning / Squall",
    "5": "Hailstorm",
    "6": "Dust Storm",
    "7": "Dust Raising Winds",
    "8": "Strong Surface Winds",
    "9": "Heat Wave",
    "10": "Hot Day",
    "11": "Warm Night",
    "12": "Cold Wave",
    "13": "Cold Day",
    "14": "Ground Frost",
    "15": "Fog",
    "16": "Very Heavy Rain",
    "17": "Extremely Heavy Rain",
}

COLOR_LEVELS = {
    "1": "RED",
    "2": "ORANGE",
    "3": "YELLOW",
    "4": "GREEN",
}


def _records(payload: Any) -> list[dict]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "records", "result", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    if any(str(key).lower() in {"district", "obj_id", "date"} for key in payload):
        return [payload]
    return []


def _field(row: dict, *names: str):
    lowered = {str(key).lower(): value for key, value in row.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def _city_match(city: str, row: dict) -> bool:
    aliases = CITY_DISTRICT_ALIASES.get(city)
    if aliases is None:
        raise ValueError(f"IMD context requires one of {sorted(CITY_DISTRICT_ALIASES)}")
    district = str(_field(row, "district", "district_name", "name") or "").strip().lower()
    return district in aliases or any(alias in district for alias in aliases)


def normalize_warning_record(row: dict) -> dict:
    normalized = {
        "district": _field(row, "district", "district_name", "name"),
        "issued_date": _field(row, "date"),
        "issued_utc": _field(row, "utc", "time"),
    }
    for day in range(1, 6):
        raw_code = _field(row, f"day_{day}", f"day{day}")
        raw_color = _field(row, f"day{day}_color", f"day_{day}_color")
        codes = [part.strip() for part in str(raw_code or "").split(",") if part.strip()]
        normalized[f"day_{day}_warnings"] = ", ".join(
            WARNING_CODES.get(code, f"Code {code}") for code in codes
        ) or None
        normalized[f"day_{day}_level"] = COLOR_LEVELS.get(str(raw_color).strip()) if raw_color is not None else None
    return normalized


def normalize_rainfall_record(row: dict) -> dict:
    output = dict(row)
    output["district"] = _field(row, "district", "district_name", "name")
    output["date"] = _field(row, "date")
    return output


def _record_error(result: dict, label: str, exc: Exception) -> None:
    if isinstance(exc, HTTPError) and exc.code in {401, 403}:
        result["access_status"] = "AUTHORIZATION_REQUIRED"
        result["errors"].append(
            f"{label}: HTTP {exc.code} — IMD endpoint reached, but this client/IP is not authorized for direct API access."
        )
    else:
        result["errors"].append(f"{label}: {exc}")


def fetch_imd_context(city: str, *, timeout: float = 6.0) -> dict:
    """Fetch district warnings and rainfall from official IMD endpoints.

    A 401/403 response is surfaced as AUTHORIZATION_REQUIRED rather than being
    presented as a generic network failure. No TLS verification is disabled and
    no observations are fabricated when direct API access is unavailable.
    """
    if city not in CITY_DISTRICT_ALIASES:
        raise ValueError(f"IMD context requires one of {sorted(CITY_DISTRICT_ALIASES)}")

    result = {
        "source": "India Meteorological Department (IMD)",
        "mode": "DEMO",
        "access_status": "UNAVAILABLE",
        "stale": False,
        "warnings": [],
        "rainfall": [],
        "errors": [],
        "warning_source_url": IMD_WARNING_URL,
        "rainfall_source_url": IMD_RAINFALL_URL,
    }
    modes: list[str] = []
    stale = False

    try:
        warning_env = fetch_json_with_cache(
            source="IMD District-wise Warning API",
            url=IMD_WARNING_URL,
            cache_path=Path("data/cache/imd") / "district_warnings.json",
            timeout=timeout,
        )
        result["warnings"] = [normalize_warning_record(row) for row in _records(warning_env.payload) if _city_match(city, row)]
        result["warning_fetched_at"] = warning_env.fetched_at
        modes.append(warning_env.mode)
        stale = stale or warning_env.stale
    except Exception as exc:
        _record_error(result, "Warning API", exc)

    try:
        rainfall_env = fetch_json_with_cache(
            source="IMD District-wise Rainfall API",
            url=IMD_RAINFALL_URL,
            cache_path=Path("data/cache/imd") / "district_rainfall.json",
            timeout=timeout,
        )
        result["rainfall"] = [normalize_rainfall_record(row) for row in _records(rainfall_env.payload) if _city_match(city, row)]
        result["rainfall_fetched_at"] = rainfall_env.fetched_at
        modes.append(rainfall_env.mode)
        stale = stale or rainfall_env.stale
    except Exception as exc:
        _record_error(result, "Rainfall API", exc)

    if modes:
        result["mode"] = "CACHED" if "CACHED" in modes else "LIVE"
        result["access_status"] = "AVAILABLE"
    result["stale"] = stale
    return result
