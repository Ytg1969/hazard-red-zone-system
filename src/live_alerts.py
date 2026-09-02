"""Optional disaster-alert feed adapter with strict LIVE/CACHED/DEMO labeling.

Configure a verified public CAP/RSS feed through SIH_SACHET_FEED_URL before
presenting the source as LIVE. The NDMA SACHET integration guide requires ETag
revalidation for CAP XML; the shared live-data layer follows that behavior and
uses a confirmed-current cache on HTTP 304.

When no verified feed is configured, this adapter returns an explicit empty
UNCONFIGURED state rather than fabricating demonstration alerts.
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path

from src.live_data import DataEnvelope, demo_envelope, fetch_text_with_etag_cache


FEED_URL_ENV_VAR = "SIH_SACHET_FEED_URL"
DEFAULT_CACHE_PATH = "data/cache/alerts/sachet_latest.json"
CAP_NAMESPACE = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}


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
                "event": info.findtext("cap:event", default="Unknown Event", namespaces=CAP_NAMESPACE),
                "severity": info.findtext("cap:severity", default="Unknown", namespaces=CAP_NAMESPACE),
                "urgency": info.findtext("cap:urgency", default=None, namespaces=CAP_NAMESPACE),
                "area": area.findtext("cap:areaDesc", default="Unspecified", namespaces=CAP_NAMESPACE)
                if area is not None
                else "Unspecified",
                "headline": info.findtext("cap:headline", default=None, namespaces=CAP_NAMESPACE),
                "published": alert_elem.findtext("cap:sent", default=None, namespaces=CAP_NAMESPACE),
                "link": alert_elem.findtext("cap:web", default=None, namespaces=CAP_NAMESPACE),
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
        "etag": envelope.etag,
    }


def fetch_disaster_alerts(
    feed_url: str | None = None,
    cache_path: str | Path = DEFAULT_CACHE_PATH,
) -> dict:
    """Fetch optional alerts while preserving explicit source-mode semantics."""
    feed_url = feed_url or os.getenv(FEED_URL_ENV_VAR)
    if not feed_url:
        envelope = demo_envelope("NDMA SACHET (verified feed not configured)", [])
        return {
            **_envelope_summary(envelope),
            "alerts": [],
            "access_status": "UNCONFIGURED",
            "error": "SIH_SACHET_FEED_URL is not configured with a verified CAP/RSS feed.",
        }

    if not str(feed_url).lower().startswith("https://"):
        envelope = demo_envelope("NDMA SACHET (invalid feed configuration)", [])
        return {
            **_envelope_summary(envelope),
            "alerts": [],
            "access_status": "INVALID_CONFIGURATION",
            "error": "SACHET feed URL must use HTTPS.",
        }

    try:
        envelope = fetch_text_with_etag_cache(
            source="Configured NDMA SACHET-compatible disaster alert feed",
            url=feed_url,
            cache_path=cache_path,
        )
        alerts = parse_alert_feed(str(envelope.payload))
        return {
            **_envelope_summary(envelope),
            "alerts": alerts,
            "access_status": "AVAILABLE",
        }
    except Exception as exc:
        envelope = demo_envelope("NDMA SACHET feed unavailable", [])
        return {
            **_envelope_summary(envelope),
            "alerts": [],
            "access_status": "UNAVAILABLE",
            "error": str(exc),
        }
