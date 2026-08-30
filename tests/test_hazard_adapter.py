import pandas as pd
import pytest

from src.hazard_adapter import normalize_hazard_classes, validate_class_score_mapping


def _layer(classes):
    return pd.DataFrame({"hazard_class": classes, "geometry": [object() for _ in classes]})


def test_validate_mapping_requires_0_to_100_scores():
    with pytest.raises(ValueError, match="between 0 and 100"):
        validate_class_score_mapping({"High": 120})


def test_normalize_hazard_classes_preserves_source_class_and_provenance():
    layer = _layer(["High", "Moderate"])
    normalized = normalize_hazard_classes(
        layer,
        class_field="hazard_class",
        class_to_score={"High": 80, "Moderate": 55},
        source_name="Verified Authority Layer",
        hazard_type="flood",
    )
    assert normalized["hazard_score"].tolist() == [80.0, 55.0]
    assert normalized["source_hazard_class"].tolist() == ["High", "Moderate"]
    assert set(normalized["source"]) == {"Verified Authority Layer"}
    assert set(normalized["hazard_type"]) == {"flood"}


def test_normalize_hazard_classes_rejects_unmapped_source_values():
    layer = _layer(["High", "Extreme"])
    with pytest.raises(ValueError, match="unmapped hazard classes"):
        normalize_hazard_classes(
            layer,
            class_field="hazard_class",
            class_to_score={"High": 80},
            source_name="Verified Authority Layer",
            hazard_type="flood",
        )


def test_normalize_hazard_classes_rejects_missing_class_values():
    layer = _layer(["High", None])
    with pytest.raises(ValueError, match="cannot be missing"):
        normalize_hazard_classes(
            layer,
            class_field="hazard_class",
            class_to_score={"High": 80},
            source_name="Verified Authority Layer",
            hazard_type="flood",
        )
