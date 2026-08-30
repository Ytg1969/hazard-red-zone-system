from src.spatial_analysis import calculate_hazard_exposure, load_hazard_layer


def test_demo_hazard_layer_loads():
    hazards = load_hazard_layer("data/demo/hazards.geojson")
    assert not hazards.empty
    assert "hazard_score" in hazards.columns


def test_habitation_inside_demo_hazard_polygon_gets_score():
    hazards = load_hazard_layer("data/demo/hazards.geojson")
    habitation = {"latitude": 20.2700, "longitude": 85.8400}
    result = calculate_hazard_exposure(habitation, hazards)
    assert result["inside_hazard_zone"] is True
    assert result["hazard_score"] >= 70
    assert result["distance_to_hazard_km"] == 0.0
