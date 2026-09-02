from src.ogc_sources import build_wms_capabilities_url, parse_wms_capabilities


SAMPLE_WMS = """<?xml version='1.0' encoding='UTF-8'?>
<WMS_Capabilities version='1.3.0' xmlns='http://www.opengis.net/wms'>
  <Service>
    <Name>WMS</Name>
    <Title>Authority Hazard Service</Title>
    <Abstract>Official contextual GIS service.</Abstract>
  </Service>
  <Capability>
    <Layer>
      <Title>Root</Title>
      <Layer>
        <Name>flood_hazard</Name>
        <Title>Flood Hazard</Title>
        <Abstract>Hazard classes require calibration before analytical use.</Abstract>
        <CRS>EPSG:4326</CRS>
        <CRS>EPSG:3857</CRS>
        <EX_GeographicBoundingBox>
          <westBoundLongitude>76.0</westBoundLongitude>
          <eastBoundLongitude>78.0</eastBoundLongitude>
          <southBoundLatitude>10.0</southBoundLatitude>
          <northBoundLatitude>12.0</northBoundLatitude>
        </EX_GeographicBoundingBox>
      </Layer>
      <Layer>
        <Name>landslide_inventory</Name>
        <Title>Landslide Inventory</Title>
        <SRS>EPSG:4326</SRS>
      </Layer>
    </Layer>
  </Capability>
</WMS_Capabilities>
"""


def test_build_wms_capabilities_url_preserves_vendor_query():
    url = build_wms_capabilities_url("https://example.gov.in/geoserver/wms?token=public&request=GetMap")
    assert url.startswith("https://example.gov.in/geoserver/wms?")
    assert "token=public" in url
    assert "service=WMS" in url
    assert "request=GetCapabilities" in url
    assert "GetMap" not in url


def test_build_wms_capabilities_url_requires_https():
    try:
        build_wms_capabilities_url("http://example.gov.in/wms")
    except ValueError as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("HTTP WMS URL should be rejected")


def test_parse_wms_capabilities_extracts_layers_and_provenance():
    parsed = parse_wms_capabilities(SAMPLE_WMS)
    assert parsed["version"] == "1.3.0"
    assert parsed["service_title"] == "Authority Hazard Service"
    assert parsed["layer_count"] == 2
    flood = parsed["layers"][0]
    assert flood["name"] == "flood_hazard"
    assert flood["crs"] == ["EPSG:3857", "EPSG:4326"]
    assert flood["geographic_bbox"]["west"] == 76.0


def test_parse_wms_capabilities_rejects_non_wms_xml():
    try:
        parse_wms_capabilities("<root><Layer><Name>x</Name></Layer></root>")
    except ValueError as exc:
        assert "unexpected WMS" in str(exc)
    else:
        raise AssertionError("Non-WMS XML should be rejected")
