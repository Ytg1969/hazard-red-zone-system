from pathlib import Path

import pandas as pd


HABITATION_REQUIRED = {
    "habitation_id",
    "name",
    "latitude",
    "longitude",
    "population",
    "children_population",
    "elderly_population",
}

SHELTER_REQUIRED = {
    "shelter_id",
    "name",
    "latitude",
    "longitude",
    "total_capacity",
    "current_occupancy",
}

HABITATION_NUMERIC = {
    "latitude",
    "longitude",
    "population",
    "children_population",
    "elderly_population",
}

SHELTER_NUMERIC = {
    "latitude",
    "longitude",
    "total_capacity",
    "current_occupancy",
}


def validate_columns(df: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def _coerce_numeric(df: pd.DataFrame, columns: set[str], label: str) -> pd.DataFrame:
    df = df.copy()
    for column in columns:
        try:
            df[column] = pd.to_numeric(df[column], errors="raise")
        except Exception as exc:
            raise ValueError(f"{label}.{column} must be numeric") from exc
    return df


def _validate_coordinates(df: pd.DataFrame, label: str) -> None:
    if not df["latitude"].between(-90, 90).all():
        raise ValueError(f"{label}.latitude must be between -90 and 90")
    if not df["longitude"].between(-180, 180).all():
        raise ValueError(f"{label}.longitude must be between -180 and 180")


def validate_habitations(df: pd.DataFrame) -> pd.DataFrame:
    validate_columns(df, HABITATION_REQUIRED, "habitations")
    df = _coerce_numeric(df, HABITATION_NUMERIC, "habitations")
    _validate_coordinates(df, "habitations")

    if df["habitation_id"].astype(str).duplicated().any():
        raise ValueError("habitation_id values must be unique")

    non_negative = ["population", "children_population", "elderly_population"]
    if (df[non_negative] < 0).any().any():
        raise ValueError("habitation population fields cannot be negative")

    if ((df["children_population"] + df["elderly_population"]) > df["population"]).any():
        raise ValueError("children + elderly population cannot exceed total population")

    return df


def validate_shelters(df: pd.DataFrame) -> pd.DataFrame:
    validate_columns(df, SHELTER_REQUIRED, "shelters")
    df = _coerce_numeric(df, SHELTER_NUMERIC, "shelters")
    _validate_coordinates(df, "shelters")

    if df["shelter_id"].astype(str).duplicated().any():
        raise ValueError("shelter_id values must be unique")

    if (df[["total_capacity", "current_occupancy"]] < 0).any().any():
        raise ValueError("shelter capacity and occupancy cannot be negative")

    return df


def load_habitations(path="data/processed/habitations.csv") -> pd.DataFrame:
    df = pd.read_csv(Path(path))
    return validate_habitations(df)


def load_shelters(path="data/processed/shelters.csv") -> pd.DataFrame:
    df = pd.read_csv(Path(path))
    return validate_shelters(df)
