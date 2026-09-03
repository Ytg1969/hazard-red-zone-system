from io import BytesIO

import pandas as pd

from src import operational_sources
from src.live_data import DataEnvelope


def _xlsx_bytes(frame: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False)
    return buffer.getvalue()


def test_remote_habitation_xlsx_uses_binary_fetcher(monkeypatch, tmp_path):
    frame = pd.DataFrame([
        {
            "habitation_id": "H1",
            "name": "Village",
            "latitude": 20.0,
            "longitude": 85.0,
            "population": 1000,
            "children_population": 180,
            "elderly_population": 90,
        }
    ])
    payload = _xlsx_bytes(frame)

    monkeypatch.setattr(
        operational_sources,
        "fetch_bytes_with_cache",
        lambda **kwargs: DataEnvelope(
            source="test", mode="LIVE", fetched_at="2026-09-03T00:00:00+00:00",
            payload=payload, source_url=kwargs["url"],
        ),
    )
    monkeypatch.setattr(
        operational_sources,
        "fetch_text_with_cache",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("text fetcher must not be used for XLSX")),
    )

    result = operational_sources.fetch_operational_habitations(
        "https://example.test/habitations.xlsx",
        cache_path=tmp_path / "habitations.bin",
    )
    assert result["format"] == "xlsx"
    assert result["mode"] == "LIVE"
    assert result["data"].iloc[0]["habitation_id"] == "H1"
    assert result["data"].iloc[0]["data_mode"] == "LIVE"


def test_remote_schema_preview_supports_xlsx(monkeypatch, tmp_path):
    payload = _xlsx_bytes(pd.DataFrame([{"Village Code": "123", "Persons": 1500}]))
    monkeypatch.setattr(
        operational_sources,
        "fetch_bytes_with_cache",
        lambda **kwargs: DataEnvelope(
            source="test", mode="CACHED", fetched_at="2026-09-03T00:00:00+00:00",
            payload=payload, stale=True, source_url=kwargs["url"],
        ),
    )
    result = operational_sources.fetch_operational_preview(
        "https://example.test/download.xlsx",
        cache_path=tmp_path / "preview.bin",
    )
    assert result["format"] == "xlsx"
    assert result["stale"] is True
    assert list(result["data"].columns) == ["Village Code", "Persons"]
