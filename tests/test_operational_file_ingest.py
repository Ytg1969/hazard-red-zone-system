import io

import pandas as pd
import pytest

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
    with pytest.raises(ValueError, match="Point geometry"):
        read_operational_upload(Upload("habitations.geojson", payload))


def test_xlsx_upload_reads_first_worksheet():
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"Village Code": [101], "Village Name": ["Alpha"]}).to_excel(writer, sheet_name="Data", index=False)
        pd.DataFrame({"Ignored": [1]}).to_excel(writer, sheet_name="Notes", index=False)
    df = read_operational_upload(Upload("authority.xlsx", buffer.getvalue()))
    assert list(df.columns) == ["Village Code", "Village Name"]
    assert df.iloc[0]["Village Name"] == "Alpha"


def test_empty_xlsx_first_sheet_is_rejected():
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame().to_excel(writer, sheet_name="Empty", index=False)
    with pytest.raises(ValueError, match="contains no rows"):
        read_operational_upload(Upload("empty.xlsx", buffer.getvalue()))


def test_legacy_xls_extension_is_rejected():
    with pytest.raises(ValueError, match="CSV, XLSX, GeoJSON, or JSON"):
        read_operational_upload(Upload("data.xls", b"not xls"))
