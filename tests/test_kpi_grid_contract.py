from pathlib import Path

from src import ui_theme


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "src/ui_theme.py"


def test_kpi_strip_renders_semantic_escaped_cards(monkeypatch):
    captured = {}

    def fake_markdown(text, **kwargs):
        captured["text"] = text
        captured["kwargs"] = kwargs

    monkeypatch.setattr(ui_theme.st, "markdown", fake_markdown)
    ui_theme.render_kpi_strip([
        ("<Locations>", "1,250", "HIGH + CRITICAL"),
        ("Capacity", "3,000", None),
    ])

    rendered = captured["text"]
    assert "hz-kpi-grid" in rendered
    assert "role='group'" in rendered
    assert "&lt;Locations&gt;" in rendered
    assert "<Locations>" not in rendered
    assert "HIGH + CRITICAL" in rendered
    assert captured["kwargs"]["unsafe_allow_html"] is True


def test_kpi_grid_uses_two_columns_on_phones():
    text = THEME.read_text(encoding="utf-8")
    assert ".hz-kpi-grid" in text
    assert "grid-template-columns:repeat(auto-fit,minmax(145px,1fr))" in text
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in text
