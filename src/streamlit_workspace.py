"""Fast Streamlit-side resolution of the active operational workspace.

Session uploads take precedence. When both configured HTTPS operational feeds are
available, a server-side cached fetch can bootstrap new browser sessions without
requiring the operator to re-upload the same authority datasets on every page.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from src.operational_sources import (
    configured_operational_urls,
    fetch_operational_habitations,
    fetch_operational_shelters,
)
from src.operational_workspace import restore_workspace, serialize_workspace


@st.cache_data(ttl=300, show_spinner=False)
def _cached_configured_workspace(habitation_url: str, shelter_url: str) -> dict[str, Any]:
    """Fetch configured operational feeds once per server cache window."""
    h_result = fetch_operational_habitations(habitation_url)
    s_result = fetch_operational_shelters(shelter_url)
    payload = serialize_workspace(
        h_result["data"],
        s_result["data"],
        label="Configured operational feeds",
    )
    return {
        "payload": payload,
        "feed_status": {
            "habitations": {k: h_result[k] for k in ["mode", "stale", "fetched_at", "source_url"]},
            "shelters": {k: s_result[k] for k in ["mode", "stale", "fetched_at", "source_url"]},
        },
    }


def resolve_operational_workspace(*, auto_configured: bool = True) -> dict[str, Any] | None:
    """Return validated operational data for the current Streamlit session.

    Resolution order:
    1. Existing browser-session workspace (uploads or prior feed activation).
    2. Configured HTTPS feeds, cached for five minutes, when enabled.
    3. None, allowing the caller to expose an explicit DEMO fallback.
    """
    payload = st.session_state.get("operational_workspace")
    if payload:
        habitations, shelters = restore_workspace(payload)
        return {"payload": payload, "habitations": habitations, "shelters": shelters, "origin": "session"}

    if not auto_configured:
        return None

    configured = configured_operational_urls()
    habitation_url = configured.get("habitations")
    shelter_url = configured.get("shelters")
    if not (habitation_url and shelter_url):
        return None

    bundle = _cached_configured_workspace(str(habitation_url), str(shelter_url))
    payload = bundle["payload"]
    st.session_state["operational_workspace"] = payload
    st.session_state["operational_feed_status"] = bundle["feed_status"]
    habitations, shelters = restore_workspace(payload)
    return {"payload": payload, "habitations": habitations, "shelters": shelters, "origin": "configured_feeds"}


def active_workspace_label(resolved: dict[str, Any] | None) -> str | None:
    if not resolved:
        return None
    return str(resolved["payload"].get("label") or "Operational dataset")
