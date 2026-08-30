"""Optional ML validation utilities for SIH26191.

This module is deliberately separate from the core risk engine. The operational
application must not depend on ML, and model metrics must not be presented as
scientific validation unless the training data has credible historical labels
and a documented leakage-safe evaluation protocol.
"""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split


DEFAULT_FEATURES = [
    "hazard_score",
    "exposure_score",
    "vulnerability_score",
    "accessibility_score",
]


def train_validation_model(
    data: pd.DataFrame,
    *,
    target_column: str,
    feature_columns: list[str] | None = None,
    test_size: float = 0.25,
    random_state: int = 26191,
) -> dict:
    feature_columns = feature_columns or DEFAULT_FEATURES
    missing = [column for column in [*feature_columns, target_column] if column not in data.columns]
    if missing:
        raise ValueError(f"ML dataset is missing required columns: {missing}")
    if len(data) < 20:
        raise ValueError("ML validation requires at least 20 labelled records")

    frame = data[[*feature_columns, target_column]].dropna().copy()
    if len(frame) < 20:
        raise ValueError("ML validation requires at least 20 complete labelled records")
    if frame[target_column].nunique() < 2:
        raise ValueError("ML target must contain at least two classes")

    X = frame[feature_columns].astype(float)
    y = frame[target_column]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=random_state,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "test_records": int(len(y_test)),
    }

    if len(model.classes_) == 2 and hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(X_test)[:, 1]
        try:
            metrics["roc_auc"] = round(float(roc_auc_score(y_test, probabilities)), 4)
        except ValueError:
            metrics["roc_auc"] = None

    importances = {
        feature: round(float(value), 4)
        for feature, value in zip(feature_columns, model.feature_importances_)
    }

    return {
        "model": model,
        "metrics": metrics,
        "feature_importance": importances,
        "features": feature_columns,
        "warning": (
            "Metrics are only meaningful if labels are authoritative, temporally valid, "
            "and the evaluation split is free from spatial/temporal leakage."
        ),
    }
