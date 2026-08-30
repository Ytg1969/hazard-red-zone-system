"""Helpers for converting verified authoritative hazard classes into core hazard scores.

This module does not fetch or guess any external GIS layer. Callers must provide a
verified machine-readable layer and an explicit class-to-score mapping documented
for that source. The adapter preserves source labels and provenance while producing
the frozen 0-100 ``hazard_score`` field expected by the spatial/risk pipeline.
"""
from __future__ import annotations

from collections.abc import Mapping


def validate_class_score_mapping(mapping: Mapping[object, object]) -> dict[str, float]:
    """Validate a source-native hazard-class to 0-100 score mapping."""
    if not mapping:
        raise ValueError("hazard class mapping cannot be empty")

    normalized: dict[str, float] = {}
    for raw_class, raw_score in mapping.items():
        label = str(raw_class).strip()
        if not label:
            raise ValueError("hazard class labels cannot be empty")
        try:
            score = float(raw_score)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"hazard score for class {label!r} must be numeric") from exc
        if not 0 <= score <= 100:
            raise ValueError(f"hazard score for class {label!r} must be between 0 and 100")
        normalized[label.casefold()] = score
    return normalized


def normalize_hazard_classes(
    gdf,
    *,
    class_field: str,
    class_to_score: Mapping[object, object],
    source_name: str,
    hazard_type: str,
):
    """Return a copy of a verified vector hazard layer with core fields added.

    Required behavior:
    - input must have geometry and the named source-native class field;
    - every non-null source class must exist in the explicit mapping;
    - geometry and source-native class values are preserved;
    - ``hazard_score``, ``source`` and ``hazard_type`` are added for the existing
      spatial exposure engine.

    Unknown source classes are rejected rather than guessed or silently mapped.
    """
    if not str(source_name).strip():
        raise ValueError("source_name is required")
    if not str(hazard_type).strip():
        raise ValueError("hazard_type is required")
    if class_field not in gdf.columns:
        raise ValueError(f"hazard layer is missing class field: {class_field}")
    if "geometry" not in gdf.columns:
        raise ValueError("hazard layer must contain geometry")

    mapping = validate_class_score_mapping(class_to_score)
    result = gdf.copy()
    labels = result[class_field].astype("string").str.strip()

    missing_mask = labels.isna() | labels.eq("")
    if missing_mask.any():
        raise ValueError("hazard class values cannot be missing")

    keys = labels.str.casefold()
    unknown = sorted(set(labels[~keys.isin(mapping)].tolist()))
    if unknown:
        raise ValueError(f"unmapped hazard classes: {unknown}")

    result["hazard_score"] = keys.map(mapping).astype(float)
    result["source"] = str(source_name).strip()
    result["hazard_type"] = str(hazard_type).strip()
    result["source_hazard_class"] = labels
    return result
