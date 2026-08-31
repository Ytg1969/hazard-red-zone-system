from src.batch_relocation import plan_batch_relocation
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data, load_demo_hazards


def test_batch_relocation_never_crosses_demo_city():
    habitations_raw, shelters_raw = load_demo_data()
    habitations = enrich_habitations(habitations_raw, hazard_data=load_demo_hazards(), hazard_type="combined")
    shelters = enrich_shelters(shelters_raw)
    plan = plan_batch_relocation(habitations, shelters, priorities=("IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM"))
    shelter_city = dict(zip(shelters["shelter_id"], shelters["demo_city"]))
    habitation_city = dict(zip(habitations["habitation_id"], habitations["demo_city"]))
    for allocation in plan["allocations"]:
        assert shelter_city[allocation["shelter_id"]] == habitation_city[allocation["habitation_id"]]


def test_batch_relocation_population_accounting_still_holds():
    habitations_raw, shelters_raw = load_demo_data()
    habitations = enrich_habitations(habitations_raw, hazard_type="combined")
    shelters = enrich_shelters(shelters_raw)
    plan = plan_batch_relocation(habitations, shelters, priorities=("IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM"))
    assert plan["allocated_population"] + plan["remaining_deficit"] == plan["required_population"]
