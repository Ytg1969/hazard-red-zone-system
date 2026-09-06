from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "odisha_flood_hazard_calibration_evidence.md"
HAZARD_CONTRACT = ROOT / "docs" / "operational_hazard_feed.md"


def test_odisha_evidence_records_authoritative_sources_and_period():
    text = EVIDENCE.read_text(encoding="utf-8")
    assert "EVIDENCE VERIFIED · ANALYTICAL CUTOVER BLOCKED" in text
    assert "https://www.osdma.org/wp-content/uploads/2019/09/Flood-Hazard-Atlas.pdf" in text
    assert "https://bhuvan-app1.nrsc.gov.in/disaster/usrtasks/flood/doc/or-hz.pdf" in text
    assert "2001–2018" in text
    assert "about 100" not in text.lower() or "satellite" in text.lower()


def test_odisha_source_classes_and_puri_summary_are_preserved():
    text = EVIDENCE.read_text(encoding="utf-8")
    required = [
        "Very Low | 1 time | 1",
        "Low | 2–4 times | 2",
        "Moderate | 5–6 times | 3",
        "High | 7–9 times | 4",
        "Very High | 10–14 times | 5",
        "347,900 ha",
        "185,028 ha",
        "53%",
        "atlas rank: **5**",
        "39,583",
        "57,053",
        "26,364",
        "35,187",
        "26,841",
    ]
    for fragment in required:
        assert fragment in text


def test_odisha_evidence_does_not_claim_calibrated_machine_readable_cutover():
    text = EVIDENCE.read_text(encoding="utf-8")
    required_boundaries = [
        "No source-class → 0–100 mapping is approved",
        "exact official WMS/WMTS/WFS/other machine-readable **Odisha 2001–2018 layer identifier**",
        "Do not infer `or_hz`, `od_hz`, or any other Odisha identifier",
        "calibration evidence only",
        "must remain false/unset",
    ]
    for fragment in required_boundaries:
        assert fragment in text


def test_hazard_feed_contract_links_odisha_evidence_without_activation():
    text = HAZARD_CONTRACT.read_text(encoding="utf-8")
    assert "docs/odisha_flood_hazard_calibration_evidence.md" in text
    assert "does **not** authorize analytical activation" in text
    assert "Do not infer a WMS layer name from other states" in text
