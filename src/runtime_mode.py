"""Runtime mode helpers shared by the Streamlit UI and data adapters."""
from __future__ import annotations

import os

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}


def offline_mode() -> bool:
    """Return True when external network activity must be suppressed."""
    return os.getenv("SIH_OFFLINE_MODE", "").strip().lower() in _TRUE_VALUES


def runtime_mode_label() -> str:
    return "OFFLINE" if offline_mode() else "CONNECTED"
