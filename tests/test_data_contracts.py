import pandas as pd
from src.preprocessing import validate_columns, HABITATION_REQUIRED, SHELTER_REQUIRED


def test_habitation_contract_accepts_required_columns():
    df = pd.DataFrame(columns=sorted(HABITATION_REQUIRED))
    validate_columns(df, HABITATION_REQUIRED, "habitations")


def test_shelter_contract_accepts_required_columns():
    df = pd.DataFrame(columns=sorted(SHELTER_REQUIRED))
    validate_columns(df, SHELTER_REQUIRED, "shelters")
