from src.bhuvan_layers import FLOOD_ANNUAL_WMS, FLOOD_HAZARD_WMS, layers_for_city


def test_verified_bhuvan_city_layers_are_context_only_registry():
    guwahati = layers_for_city("Guwahati")
    puri = layers_for_city("Puri")
    chennai = layers_for_city("Chennai")

    assert any(item["layer"] == "as_hz" and item["service_url"] == FLOOD_HAZARD_WMS for item in guwahati)
    assert any(item["layer"] == "or_cyclone" and item["service_url"] == FLOOD_ANNUAL_WMS for item in puri)
    assert any(item["layer"] == "tn_011112_flood" for item in chennai)
    assert layers_for_city("All Demo Cities") == []
