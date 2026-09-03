"""Deterministic readiness checks for removing bundled DEMO fallbacks.

This module does not certify data as authoritative. It only evaluates whether
an already-validated operational workspace satisfies the project's explicit
technical cutover gates. Source ownership and administrative approval remain
human-governance requirements.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from src.data_contracts import assess_habitation_dataset, assess_shelter_dataset
from src.operational_workspace import dataset_mode


def assess_cutover_readiness(
    habitations: pd.DataFrame,
    shelters: pd.DataFrame,
    *,
    hazard_ready: bool,
) -> dict[str, Any]:
    """Assess whether synthetic analytical fallbacks can be disabled safely.

    Required technical gates intentionally exceed the minimum ingestion schema:
    - both operational datasets are non-empty and structurally valid;
    - neither dataset is DEMO/UNVERIFIED;
    - recommended provenance fields are present;
    - all carrying-capacity evidence fields are present;
    - an explicitly reviewed/calibrated hazard source is available.

    Passing these gates means the application is technically ready for strict
    operational mode. It is not a government certification of the underlying
    data or a substitute for field/administrative review.
    """
    h = assess_habitation_dataset(habitations)
    s = assess_shelter_dataset(shelters)
    habitation_mode = dataset_mode(habitations)
    shelter_mode = dataset_mode(shelters)

    checks = [
        {
            "key": "habitation_schema",
            "label": "Habitation schema and integrity",
            "pass": bool(len(habitations) and h["production_schema_valid"]),
            "detail": f"{len(habitations)} record(s); required fields, IDs, coordinates and population integrity checked.",
        },
        {
            "key": "shelter_schema",
            "label": "Relocation-site schema and integrity",
            "pass": bool(len(shelters) and s["production_schema_valid"]),
            "detail": f"{len(shelters)} record(s); required fields, IDs, coordinates and capacity integrity checked.",
        },
        {
            "key": "operational_modes",
            "label": "Operational provenance mode",
            "pass": habitation_mode in {"LIVE", "CACHED"} and shelter_mode in {"LIVE", "CACHED"},
            "detail": f"Habitations={habitation_mode}; relocation sites={shelter_mode}. DEMO/UNVERIFIED blocks cutover.",
        },
        {
            "key": "provenance_fields",
            "label": "Source provenance fields",
            "pass": bool(h["provenance_complete"] and s["provenance_complete"]),
            "detail": "Requires data_mode, data_timestamp and source_context on both operational datasets.",
        },
        {
            "key": "capacity_evidence",
            "label": "Carrying-capacity evidence",
            "pass": float(s["resource_completeness_pct"]) >= 100.0,
            "detail": f"Resource-field completeness={float(s['resource_completeness_pct']):.0f}% (water, sanitation, access, safety, accessibility).",
        },
        {
            "key": "calibrated_hazard",
            "label": "Reviewed analytical hazard source",
            "pass": bool(hazard_ready),
            "detail": "Requires an explicitly reviewed/calibrated hazard source or equivalent approved analytical hazard evidence.",
        },
    ]

    passed = sum(1 for check in checks if check["pass"])
    total = len(checks)
    return {
        "ready_for_demo_removal": passed == total,
        "passed_checks": passed,
        "total_checks": total,
        "readiness_pct": round(100.0 * passed / total, 1) if total else 0.0,
        "habitation_mode": habitation_mode,
        "shelter_mode": shelter_mode,
        "habitation_assessment": h,
        "shelter_assessment": s,
        "checks": checks,
        "governance_note": "Technical readiness does not certify source authority or approve relocation decisions.",
    }
