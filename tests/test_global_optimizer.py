from src.global_optimizer import optimize_relocation_flow
from src.pipeline import enrich_habitations, enrich_shelters, load_demo_data


def test_global_optimizer_is_capacity_safe_and_city_local():
    habitations_raw, shelters_raw = load_demo_data()
    habitations = enrich_habitations(habitations_raw, hazard_type="combined")
    shelters = enrich_shelters(shelters_raw)
    plan = optimize_relocation_flow(habitations, shelters, priorities=("IMMEDIATE", "SHORT_TERM", "MEDIUM_TERM"))
    assert plan["allocated_population"] + plan["remaining_deficit"] == plan["required_population"]

    shelter_city = dict(zip(shelters["shelter_id"], shelters["demo_city"]))
    habitation_city = dict(zip(habitations["habitation_id"], habitations["demo_city"]))
    available = dict(zip(shelters["shelter_id"], shelters["available_capacity"]))
    assigned = {}
    for item in plan["allocations"]:
        assert shelter_city[item["shelter_id"]] == habitation_city[item["habitation_id"]]
        assigned[item["shelter_id"]] = assigned.get(item["shelter_id"], 0) + item["assigned_population"]
    for shelter_id, population in assigned.items():
        assert population <= available[shelter_id]
