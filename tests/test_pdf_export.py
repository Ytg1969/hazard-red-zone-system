from src.report_generator import generate_action_plan_pdf


def test_action_plan_pdf_is_valid_binary_payload():
    pdf = generate_action_plan_pdf(
        habitation={
            "name": "Coastal A & B <Test>",
            "habitation_id": "H-001",
            "population": 1200,
            "relocation_priority": "IMMEDIATE",
        },
        risk={
            "risk_score": 82.4,
            "risk_level": "CRITICAL",
            "drivers": ["Hazard exposure", "Evacuation difficulty"],
        },
        relocation={
            "shelter_name": "Shelter & Relief Centre <1>",
            "distance_km": 4.2,
            "travel_time_min": 10.0,
            "routing_mode": "cached_osm_graph",
            "available_capacity": 900,
            "capacity_validation_status": "VALIDATED",
            "suitability_score": 88.0,
        },
        allocation={
            "required_population": 1200,
            "allocated_population": 900,
            "remaining_deficit": 300,
            "allocations": [
                {
                    "shelter_name": "Shelter & Relief Centre <1>",
                    "assigned_population": 900,
                    "distance_km": 4.2,
                    "suitability_score": 88.0,
                }
            ],
        },
        data_mode="DEMO",
    )

    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
