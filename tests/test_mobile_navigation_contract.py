from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "src/ui_theme.py"


def test_mobile_navigation_keeps_four_field_actions():
    text = THEME.read_text(encoding="utf-8")
    required = [
        '("Command", "app.py", "⌂")',
        '("Map", "pages/2_Red_Zone_Map.py", "◉")',
        '("Relocate", "pages/4_Relocation_Planner.py", "⇢")',
        '("Brief", "pages/13_Briefing.py", "▤")',
        'st.container(key="hz_mobile_nav")',
    ]
    for fragment in required:
        assert fragment in text

    mobile_block = text.split("MOBILE_NAV = [", 1)[1].split("]", 1)[0]
    assert mobile_block.count("pages/") == 3
    assert mobile_block.count("app.py") == 1
    assert "Live_Data_Context" not in mobile_block


def test_mobile_navigation_is_phone_only_and_safe_area_aware():
    text = THEME.read_text(encoding="utf-8")
    assert ".st-key-hz_mobile_nav { display:none; }" in text
    assert "@media (max-width:720px)" in text
    assert "position:fixed" in text
    assert "env(safe-area-inset-bottom)" in text
    assert "padding:.62rem .62rem 6.15rem" in text
