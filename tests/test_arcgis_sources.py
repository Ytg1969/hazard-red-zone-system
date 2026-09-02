from src.arcgis_sources import geojson_query_url, layer_url, metadata_url, parse_arcgis_metadata


def test_metadata_url_requires_https_and_sets_pjson():
    assert metadata_url("https://example.test/arcgis/rest/services/Hazards/FeatureServer?token=x").endswith("token=x&f=pjson")
    try:
        metadata_url("http://example.test/FeatureServer")
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("HTTP ArcGIS URL should be rejected")


def test_parse_service_metadata_discovers_layers():
    parsed = parse_arcgis_metadata({
        "serviceDescription": "District hazard service",
        "capabilities": "Map,Query,Data",
        "layers": [
            {"id": 0, "name": "Flood Hazard", "parentLayerId": -1, "defaultVisibility": True},
            {"id": 1, "name": "Landslide Susceptibility", "parentLayerId": -1, "defaultVisibility": False},
        ],
        "fullExtent": {"xmin": 70, "ymin": 8, "xmax": 90, "ymax": 30, "spatialReference": {"wkid": 4326}},
    })
    assert parsed["layer_count"] == 2
    assert parsed["supports_query"] is True
    assert parsed["extent"]["spatial_reference"] == 4326


def test_parse_layer_metadata_discovers_fields():
    parsed = parse_arcgis_metadata({
        "name": "Flood Hazard",
        "type": "Feature Layer",
        "geometryType": "esriGeometryPolygon",
        "capabilities": "Query,Extract",
        "maxRecordCount": 2000,
        "fields": [
            {"name": "HAZ_CLASS", "alias": "Hazard Class", "type": "esriFieldTypeString"},
            {"name": "SCORE", "alias": "Score", "type": "esriFieldTypeDouble"},
        ],
    })
    assert parsed["geometry_type"] == "esriGeometryPolygon"
    assert parsed["field_count"] == 2
    assert parsed["fields"][0]["name"] == "HAZ_CLASS"


def test_layer_and_geojson_query_urls_are_deterministic():
    service = "https://example.test/arcgis/rest/services/Hazards/FeatureServer"
    layer = layer_url(service, 3)
    assert layer.endswith("/FeatureServer/3")
    query = geojson_query_url(layer)
    assert query.startswith(layer + "/query?")
    assert "f=geojson" in query
    assert "returnGeometry=true" in query
