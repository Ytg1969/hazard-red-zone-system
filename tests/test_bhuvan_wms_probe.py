from scripts.bhuvan_wms_probe import parse_layers


def test_parse_layers_handles_namespaced_wms_document():
    xml = """
    <WMS_Capabilities xmlns="http://www.opengis.net/wms">
      <Capability>
        <Layer>
          <Title>Root</Title>
          <Layer><Name>flood_hazard_demo</Name><Title>Flood Hazard</Title></Layer>
          <Layer><Name>annual_2010</Name><Title>Flood Annual 2010</Title></Layer>
        </Layer>
      </Capability>
    </WMS_Capabilities>
    """
    assert parse_layers(xml) == [
        {"name": "flood_hazard_demo", "title": "Flood Hazard"},
        {"name": "annual_2010", "title": "Flood Annual 2010"},
    ]
