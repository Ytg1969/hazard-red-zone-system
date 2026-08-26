from pathlib import Path
import pandas as pd

HABITATION_REQUIRED = {
    "habitation_id", "name", "latitude", "longitude", "population",
    "children_population", "elderly_population"
}

SHELTER_REQUIRED = {
    "shelter_id", "name", "latitude", "longitude", "total_capacity",
    "current_occupancy"
}


def validate_columns(df: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"{label} is missing required columns: {missing}")


def load_habitations(path="data/processed/habitations.csv") -> pd.DataFrame:
    df = pd.read_csv(Path(path))
    validate_columns(df, HABITATION_REQUIRED, "habitations")
    return df


def load_shelters(path="data/processed/shelters.csv") -> pd.DataFrame:
    df = pd.read_csv(Path(path))
    validate_columns(df, SHELTER_REQUIRED, "shelters")
    return df
