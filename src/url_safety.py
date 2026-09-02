"""Shared validation for operator/configured public HTTPS data sources.

The app fetches URLs server-side, so obvious local/private-network targets must be
rejected before any request is attempted. This is a defense-in-depth guard for a
public Streamlit deployment; upstream networking should still restrict egress.
"""
from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


_BLOCKED_HOSTS = {"localhost", "localhost.localdomain"}
_BLOCKED_SUFFIXES = (".localhost", ".local", ".internal")


def validate_public_https_url(url: str, *, purpose: str = "source") -> str:
    value = str(url or "").strip()
    parsed = urlsplit(value)
    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError(f"{purpose} URL must be an absolute HTTPS URL")
    if parsed.username or parsed.password:
        raise ValueError(f"{purpose} URL must not embed credentials")

    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not host:
        raise ValueError(f"{purpose} URL must include a hostname")
    if host in _BLOCKED_HOSTS or host.endswith(_BLOCKED_SUFFIXES):
        raise ValueError(f"{purpose} URL must not target a local/private hostname")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and not address.is_global:
        raise ValueError(f"{purpose} URL must not target a private, loopback, link-local, or reserved IP address")

    return value
