import io

from src.operational_file_ingest import read_operational_upload


class Upload(io.BytesIO):
    def __init__(self, name: str, payload: bytes):
        super().__init__(payload)
        self.name = name

    def getvalue(self):
        return super().getvalue()


def test_csv_upload_reads_dataframe():
    upload = Upload("habitations.csv", b"habitation_id,name,latitude,longitude,population,children_population,elderly_population\nH1,A,10,76,100,10,5\n")
    df = read_operational_upload(upload)
    assert len(df) == 1
    assert df.iloc[0]["habitation_id"] == "H1"


def test_geojson_point_geometry_supplies_coordinates():
    payload = b'''{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"habitation_id":"H1","name":"A","population":100,"children_population":10,"elderly_population":5},"geometry":{"type":"Point","coordinates":[76.5,10.5]}}]}'''
    df = read_operational_upload(Upload("habitations.geojson", payload))
    assert float(df.iloc[0]["longitude"]) == 76.5
    assert float(df.iloc[0]["latitude"]) == 10.5


def test_geojson_rejects_non_point_geometry():
    payload = b'''{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"A"},"geometry":{"type":"Polygon","coordinates":[]}}]}'''
    try:
        read_operational_upload(Upload("habitations.geojson", payload))
    except ValueError as exc:
        assert "Point geometry" in str(exc)
    else:
        raise AssertionError("non-Point operational geometry should be rejected")


def test_unknown_extension_is_rejected():
    try:
        read_operational_upload(Upload("data.xlsx", b"not xlsx"))
    except ValueError as exc:
        assert "CSV, GeoJSON, or JSON" in str(exc)
    else:
        raise AssertionError("unsupported operational upload should be rejected")
