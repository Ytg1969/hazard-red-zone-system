"""Optional disaster-alert feed adapter with strict LIVE/CACHED/DEMO labeling.

The exact NDMA SACHET feed URL is intentionally not hardcoded. Configure a
verified public CAP/RSS feed through SIH_SACHET_FEED_URL before presenting the
source as LIVE. Without that setting, the UI receives clearly labelled DEMO
sample alerts and the core offline workflow remains unaffected.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path

from src.live_data import DataEnvelope, demo_envelope, fetch_text_with_cache


FEED_URL_ENV_VAR = "SIH_SACHET_FEED_URL"
DEFAULT_CACHE_PATH = "data/cache/alerts/sachet_latest.json"
CAP_NAMESPACE = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}

_DEMO_ALERTS = [
    {
        "event": "Flood Warning (demonstration)",
        "severity": "Severe",
        "urgency": "Expected",
        "area": "Demonstration district",
        "headline": "Illustrative alert used to demonstrate how an official CAP/RSS warning would appear.",
        "published": None,
        "link": None,
    },
    {
        "event": "Heavy Rainfall Advisory (demonstration)",
        "severity": "Moderate",
        "urgency": "Expected",
        "area": "Demonstration district",
        "headline": "No live alert feed is configured; this row is synthetic UI fallback content.",
        "published": None,
        "link": None,
    },
]


def parse_cap_alerts(xml_text: str) -> list[dict]:
    """Parse Common Alerting Protocol 1.2 XML into normalized alert records."""
    root = ET.fromstring(xml_text)
    alert_elements = root.findall(".//cap:alert", CAP_NAMESPACE)
    if not alert_elements and root.tag.endswith("alert"):
        alert_elements = [root]

    alerts: list[dict] = []
    for alert_elem in alert_elements:
        info = alert_elem.find("cap:info", CAP_NAMESPACE)
        if info is None:
            continue
        area = info.find("cap:area", CAP_NAMESPACE)
        alerts.append(
            {
                "event": info.findtext(
                    "cap:event", default="Unknown Event", namespaces=CAP_NAMESPACE
                ),
                "severity": info.findtext(
                    "cap:severity", default="Unknown", namespaces=CAP_NAMESPACE
                ),
                "urgency": info.findtext(
                    "cap:urgency", default=None, namespaces=CAP_NAMESPACE
                ),
                "area": area.findtext(
                    "cap:areaDesc", default="Unspecified", namespaces=CAP_NAMESPACE
                )
                if area is not None
                else "Unspecified",
                "headline": info.findtext(
                    "cap:headline", default=None, namespaces=CAP_NAMESPACE
                ),
                "published": alert_elem.findtext(
                    "cap:sent", default=None, namespaces=CAP_NAMESPACE
                ),
                "link": alert_elem.findtext(
                    "cap:web", default=None, namespaces=CAP_NAMESPACE
                ),
            }
        )
    return alerts


def parse_rss_alerts(xml_text: str) -> list[dict]:
    """Parse a generic RSS 2.0 feed into normalized alert records."""
    root = ET.fromstring(xml_text)
    alerts: list[dict] = []
    for item in root.findall(".//item"):
        alerts.append(
            {
                "event": item.findtext("title", default="Unknown Event"),
                "severity": None,
                "urgency": None,
                "area": None,
                "headline": item.findtext("description", default=None),
                "published": item.findtext("pubDate", default=None),
                "link": item.findtext("link", default=None),
            }
        )
    return alerts


def parse_alert_feed(xml_text: str) -> list[dict]:
    """Best-effort parse of CAP or RSS; malformed feeds return an empty list."""
    try:
        alerts = parse_cap_alerts(xml_text)
        if alerts:
            return alerts
    except ET.ParseError:
        pass

    try:
        return parse_rss_alerts(xml_text)
    except ET.ParseError:
        return []


def _envelope_summary(envelope: DataEnvelope) -> dict:
    return {
        "mode": envelope.mode,
        "fetched_at": envelope.fetched_at,
        "source": envelope.source,
        "source_url": envelope.source_url,
        "stale": envelope.stale,
    }


def fetch_disaster_alerts(
    feed_url: str | None = None,
    cache_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict:
    """Fetch optional alerts while preserving explicit source-mode semantics."""
    feed_url = feed_url or os.getenv(FEED_URL_ENV_VAR)
    if not feed_url:
        envelope = demo_envelope("NDMA SACHET-compatible alert UI (feed not configured)", _DEMO_ALERTS)
        return {**_envelope_summary(envelope), "alerts": _DEMO_ALERTS}

    try:
        envelope = fetch_text_with_cache(
            source="Configured disaster alert feed",
            url=feed_url,
            cache_path=cache_path,
        )
        alerts = parse_alert_feed(str(envelope.payload))
        return {**_envelope_summary(envelope), "alerts": alerts}
    except Exception as exc:
        envelope = demo_envelope("Disaster alert feed unavailable", _DEMO_ALERTS)
        return {
            **_envelope_summary(envelope),
            "alerts": _DEMO_ALERTS,
            "error": str(exc),
        }
