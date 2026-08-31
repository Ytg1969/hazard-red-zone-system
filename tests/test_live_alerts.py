from src.live_alerts import fetch_disaster_alerts, parse_alert_feed, parse_cap_alerts, parse_rss_alerts


SAMPLE_CAP = """<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>TEST-001</identifier>
  <sender>example@gov.in</sender>
  <sent>2026-08-29T10:00:00+05:30</sent>
  <status>Actual</status>
  <msgType>Alert</msgType>
  <scope>Public</scope>
  <info>
    <event>Flood</event>
    <urgency>Expected</urgency>
    <severity>Severe</severity>
    <certainty>Likely</certainty>
    <headline>Heavy rainfall expected to raise river levels</headline>
    <area><areaDesc>Puri, Odisha</areaDesc></area>
  </info>
  <web>https://example.gov.in/alerts/TEST-001</web>
</alert>"""

SAMPLE_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><item>
<title>Cyclone Warning</title>
<description>Cyclone warning text.</description>
<pubDate>Sat, 29 Aug 2026 10:00:00 GMT</pubDate>
<link>https://example.gov.in/alerts/1</link>
</item></channel></rss>"""


def test_parse_cap_alerts_extracts_normalized_fields():
    alerts = parse_cap_alerts(SAMPLE_CAP)
    assert len(alerts) == 1
    assert alerts[0]["event"] == "Flood"
    assert alerts[0]["severity"] == "Severe"
    assert alerts[0]["area"] == "Puri, Odisha"


def test_parse_rss_alerts_extracts_normalized_fields():
    alerts = parse_rss_alerts(SAMPLE_RSS)
    assert len(alerts) == 1
    assert alerts[0]["event"] == "Cyclone Warning"


def test_parse_alert_feed_handles_malformed_input():
    assert parse_alert_feed("not xml") == []


def test_alert_adapter_defaults_to_explicit_demo_mode(monkeypatch):
    monkeypatch.delenv("SIH_SACHET_FEED_URL", raising=False)
    result = fetch_disaster_alerts()
    assert result["mode"] == "DEMO"
    assert result["alerts"]
    assert all("demonstration" in row["event"].lower() for row in result["alerts"])
