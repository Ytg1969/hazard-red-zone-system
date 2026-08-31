import pandas as pd

from src.batch_relocation import plan_batch_relocation
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards


def _demo_inputs():
    habitations_raw, shelters_raw = load_demo_data()
    hazards = load_demo_hazards()
    habitations = enrich_habitations(habitations_raw, hazard_data=hazards)
    shelters = enrich_shelters(shelters_raw)
    return habitations, shelters


def test_batch_plan_never_double_books_shelter_capacity():
    habitations, shelters = _demo_inputs()
    result = plan_batch_relocation(habitations, shelters)

    assigned_by_shelter = {}
    for row in result["allocations"]:
        assigned_by_shelter[row["shelter_id"]] = (
            assigned_by_shelter.get(row["shelter_id"], 0) + row["assigned_population"]
        )

    available_by_shelter = dict(zip(shelters["shelter_id"], shelters["available_capacity"]))
    assert all(
        assigned <= available_by_shelter[shelter_id]
        for shelter_id, assigned in assigned_by_shelter.items()
    )


def test_batch_plan_population_accounting_is_exact():
    habitations, shelters = _demo_inputs()
    result = plan_batch_relocation(habitations, shelters)

    assert result["allocated_population"] <= result["required_population"]
    assert (
        result["allocated_population"] + result["remaining_deficit"]
        == result["required_population"]
    )
    assert sum(row["assigned_population"] for row in result["allocations"]) == result[
        "allocated_population"
    ]
    assert sum(row["unallocated_population"] for row in result["unallocated"]) == result[
        "remaining_deficit"
    ]


def test_batch_plan_respects_safety_filter():
    habitations = pd.DataFrame(
        [
            {
                "habitation_id": "H1",
                "name": "Priority Village",
                "latitude": 20.0,
                "longitude": 85.0,
                "population": 100,
                "risk_score": 90,
                "relocation_priority": "IMMEDIATE",
            }
        ]
    )
    shelters = pd.DataFrame(
        [
            {
                "shelter_id": "UNSAFE",
                "name": "Unsafe Site",
                "latitude": 20.01,
                "longitude": 85.01,
                "total_capacity": 1000,
                "current_occupancy": 0,
                "safety_score": 40,
                "accessibility_score": 100,
            },
            {
                "shelter_id": "SAFE",
                "name": "Safe Site",
                "latitude": 20.02,
                "longitude": 85.02,
                "total_capacity": 100,
                "current_occupancy": 0,
                "safety_score": 80,
                "accessibility_score": 80,
            },
        ]
    )

    result = plan_batch_relocation(habitations, shelters)
    assert result["allocated_population"] == 100
    assert {row["shelter_id"] for row in result["allocations"]} == {"SAFE"}
