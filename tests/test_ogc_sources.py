from src.ogc_sources import (
    build_wfs_capabilities_url,
    build_wfs_geojson_url,
    build_wms_capabilities_url,
    parse_wfs_capabilities,
    parse_wms_capabilities,
)


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

SAMPLE_WFS = """<?xml version='1.0' encoding='UTF-8'?>
<wfs:WFS_Capabilities version='2.0.0'
  xmlns:wfs='http://www.opengis.net/wfs/2.0'
  xmlns:ows='http://www.opengis.net/ows/1.1'>
  <ows:ServiceIdentification>
    <ows:Title>Authority Feature Service</ows:Title>
    <ows:Abstract>Official vector feature service.</ows:Abstract>
  </ows:ServiceIdentification>
  <wfs:FeatureTypeList>
    <wfs:FeatureType>
      <wfs:Name>haz:flood</wfs:Name>
      <wfs:Title>Flood Hazard</wfs:Title>
      <wfs:Abstract>Flood classes.</wfs:Abstract>
      <wfs:DefaultCRS>urn:ogc:def:crs:EPSG::4326</wfs:DefaultCRS>
      <ows:WGS84BoundingBox>
        <ows:LowerCorner>76 10</ows:LowerCorner>
        <ows:UpperCorner>78 12</ows:UpperCorner>
      </ows:WGS84BoundingBox>
    </wfs:FeatureType>
  </wfs:FeatureTypeList>
</wfs:WFS_Capabilities>
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


def test_build_wfs_capabilities_url_preserves_vendor_query():
    url = build_wfs_capabilities_url("https://example.gov.in/geoserver/wfs?token=public&request=GetFeature")
    assert "token=public" in url
    assert "service=WFS" in url
    assert "request=GetCapabilities" in url
    assert "GetFeature" not in url


def test_parse_wfs_capabilities_extracts_feature_types_and_bbox():
    parsed = parse_wfs_capabilities(SAMPLE_WFS)
    assert parsed["version"] == "2.0.0"
    assert parsed["service_title"] == "Authority Feature Service"
    assert parsed["feature_type_count"] == 1
    feature = parsed["feature_types"][0]
    assert feature["name"] == "haz:flood"
    assert feature["geographic_bbox"] == {"west": 76.0, "south": 10.0, "east": 78.0, "north": 12.0}
    assert "EPSG::4326" in feature["crs"][0]


def test_parse_wfs_capabilities_rejects_non_wfs_xml():
    try:
        parse_wfs_capabilities("<root><FeatureType><Name>x</Name></FeatureType></root>")
    except ValueError as exc:
        assert "unexpected WFS" in str(exc)
    else:
        raise AssertionError("Non-WFS XML should be rejected")


def test_build_wfs_geojson_url_is_explicit_and_bounded():
    url = build_wfs_geojson_url(
        "https://example.gov.in/geoserver/wfs?token=public",
        "haz:flood",
        count=500,
    )
    assert "token=public" in url
    assert "service=WFS" in url
    assert "request=GetFeature" in url
    assert "typeNames=haz%3Aflood" in url
    assert "outputFormat=application%2Fjson" in url
    assert "count=500" in url
