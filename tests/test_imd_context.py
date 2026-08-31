from src.imd_context import _records, _city_match, normalize_warning_record


def test_records_accepts_list_and_nested_data():
    rows = [{"District": "Puri"}]
    assert _records(rows) == rows
    assert _records({"data": rows}) == rows


def test_city_match_handles_demo_city_aliases():
    assert _city_match("Puri", {"District": "Puri"}) is True
    assert _city_match("Guwahati", {"District": "Kamrup Metropolitan"}) is True
    assert _city_match("Chennai", {"district_name": "Chennai"}) is True
    assert _city_match("Puri", {"District": "Chennai"}) is False


def test_warning_codes_and_color_levels_are_explainable():
    row = {
        "District": "Puri",
        "Date": "2026-08-31",
        "UTC": "03:00",
        "Day_1": "2,4",
        "Day1_Color": "2",
        "Day_2": "17",
        "Day2_Color": "1",
    }
    result = normalize_warning_record(row)
    assert result["district"] == "Puri"
    assert result["day_1_warnings"] == "Heavy Rain, Thunderstorm / Lightning / Squall"
    assert result["day_1_level"] == "ORANGE"
    assert result["day_2_warnings"] == "Extremely Heavy Rain"
    assert result["day_2_level"] == "RED"
