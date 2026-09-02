"""Experimental coordination grouping for map/briefing convenience.

These labels do not affect risk, shelter suitability, allocation, routing, or
evacuation decisions.
"""
from __future__ import annotations

import pandas as pd


def assign_coordination_zones(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    required = {"latitude", "longitude", "risk_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"coordination zoning missing columns: {sorted(missing)}")

    work = df.copy()
    if work.empty:
        work["coordination_zone"] = pd.Series(dtype="object")
        work["coordination_zone_status"] = pd.Series(dtype="object")
        return work

    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        work["coordination_zone"] = "Not computed"
        work["coordination_zone_status"] = "OPTIONAL_DEPENDENCY_MISSING"
        return work

    clusters = max(1, min(int(n_clusters), len(work)))
    features = work[["latitude", "longitude", "risk_score"]].astype(float)
    scaled = StandardScaler().fit_transform(features)
    labels = KMeans(n_clusters=clusters, random_state=42, n_init=10).fit_predict(scaled)

    order = (
        pd.DataFrame({"label": labels, "risk": work["risk_score"].to_numpy()})
        .groupby("label")["risk"]
        .mean()
        .sort_values(ascending=False)
        .index.tolist()
    )
    names = {label: f"Zone {chr(65 + index)}" for index, label in enumerate(order)}
    work["coordination_zone"] = [names[label] for label in labels]
    work["coordination_zone_status"] = "COMPUTED_EXPERIMENTAL"
    return work
