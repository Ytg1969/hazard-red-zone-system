"""Fast Streamlit-side resolution of the active operational workspace.

Session uploads take precedence. When configured HTTPS feeds are available,
server-side caching can bootstrap new browser sessions without repeated uploads.
A production deployment can explicitly disable synthetic demo fallbacks by
setting SIH_REQUIRE_OPERATIONAL_DATA=true.
"""
from __future__ import annotations

import os
from typing import Any

import streamlit as st

from src.operational_hazards import configured_hazard_source, fetch_configured_hazard
from src.operational_sources import configured_operational_urls, fetch_operational_habitations, fetch_operational_shelters
from src.operational_workspace import restore_workspace, serialize_workspace


REQUIRE_OPERATIONAL_ENV = "SIH_REQUIRE_OPERATIONAL_DATA"


def operational_data_required() -> bool:
    return str(os.getenv(REQUIRE_OPERATIONAL_ENV, "")).strip().lower() in {"1", "true", "yes", "required", "production"}


def _stop_missing_operational_data(message: str) -> None:
    st.error(message)
    st.info(
        "Production mode is configured to reject bundled DEMO habitations/shelters. "
        "Configure SIH_HABITATION_CSV_URL and SIH_SHELTER_CSV_URL, or activate a validated upload from Operational Data."
    )
    st.page_link("pages/9_Operational_Data.py", label="Open Operational Data", use_container_width=True)
    st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_configured_workspace(habitation_url: str, shelter_url: str) -> dict[str, Any]:
    h_result = fetch_operational_habitations(habitation_url)
    s_result = fetch_operational_shelters(shelter_url)
    payload = serialize_workspace(h_result["data"], s_result["data"], label="Configured operational feeds")
    return {
        "payload": payload,
        "feed_status": {
            "habitations": {k: h_result[k] for k in ["mode", "stale", "fetched_at", "source_url"]},
            "shelters": {k: s_result[k] for k in ["mode", "stale", "fetched_at", "source_url"]},
        },
    }


@st.cache_data(ttl=300, show_spinner=False)
def _cached_configured_hazard(hazard_url: str) -> dict[str, Any]:
    return fetch_configured_hazard(hazard_url, calibration_confirmed=True)


def resolve_operational_workspace(*, auto_configured: bool = True, enforce_required: bool = True) -> dict[str, Any] | None:
    """Return validated operational habitation/site data for the current session.

    If SIH_REQUIRE_OPERATIONAL_DATA=true and enforce_required is left enabled,
    the function stops the Streamlit page instead of permitting a DEMO fallback.
    The Operational Data management page can set enforce_required=False so an
    operator still has a recovery/upload path when a configured feed is down.
    """
    payload = st.session_state.get("operational_workspace")
    if payload:
        habitations, shelters = restore_workspace(payload)
        return {"payload": payload, "habitations": habitations, "shelters": shelters, "origin": "session"}

    if not auto_configured:
        if enforce_required and operational_data_required():
            _stop_missing_operational_data("No validated operational workspace is active.")
        return None

    configured = configured_operational_urls()
    habitation_url = configured.get("habitations")
    shelter_url = configured.get("shelters")
    if not (habitation_url and shelter_url):
        if enforce_required and operational_data_required():
            _stop_missing_operational_data("Required operational habitation/shelter feeds are not configured.")
        return None

    try:
        bundle = _cached_configured_workspace(str(habitation_url), str(shelter_url))
    except Exception as exc:
        if enforce_required and operational_data_required():
            _stop_missing_operational_data(f"Configured operational feeds could not be validated/refreshed: {exc}")
        raise

    payload = bundle["payload"]
    st.session_state["operational_workspace"] = payload
    st.session_state["operational_feed_status"] = bundle["feed_status"]
    habitations, shelters = restore_workspace(payload)
    return {"payload": payload, "habitations": habitations, "shelters": shelters, "origin": "configured_feeds"}


def resolve_operational_hazard(*, auto_configured: bool = True) -> dict[str, Any] | None:
    """Return an explicitly calibrated hazard GeoJSON from session or deployment config."""
    session_text = st.session_state.get("operational_hazard_geojson")
    if session_text:
        return {
            "geojson": str(session_text),
            "label": st.session_state.get("operational_hazard_name", "Uploaded calibrated hazard GeoJSON"),
            "mode": "SESSION",
            "stale": False,
            "origin": "session",
        }

    if not auto_configured:
        return None

    configured = configured_hazard_source()
    if not configured.get("url") or not configured.get("calibration_confirmed"):
        return None

    result = _cached_configured_hazard(str(configured["url"]))
    st.session_state["operational_hazard_feed_status"] = {
        k: result.get(k) for k in ["mode", "stale", "fetched_at", "source_url", "label", "feature_count"]
    }
    return {**result, "origin": "configured_feed"}


def active_workspace_label(resolved: dict[str, Any] | None) -> str | None:
    if not resolved:
        return None
    return str(resolved["payload"].get("label") or "Operational dataset")
