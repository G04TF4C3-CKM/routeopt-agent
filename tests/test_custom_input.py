import pytest
from src.custom_input import parse_txt_loads, parse_csv_loads, normalize_load_rows_to_scenario_text


def test_parse_txt_loads_valid():
    txt = """(1.0, 2.0), (3.0, 4.0)\n(2.0, 1.0), (4.0, 3.0)"""
    rows = parse_txt_loads(txt)
    assert rows == ["(1.0, 2.0), (3.0, 4.0)", "(2.0, 1.0), (4.0, 3.0)"]


def test_parse_txt_loads_invalid():
    txt = "invalid line"
    with pytest.raises(ValueError) as exc:
        parse_txt_loads(txt)
    assert "does not match the required format" in str(exc.value)


def test_parse_csv_loads_valid():
    csv = """pickup_x,pickup_y,dropoff_x,dropoff_y\n1.0,2.0,3.0,4.0\n2.0,1.0,4.0,3.0"""
    rows = parse_csv_loads(csv)
    assert rows == ["(1.0, 2.0), (3.0, 4.0)", "(2.0, 1.0), (4.0, 3.0)"]


def test_parse_csv_loads_invalid_header():
    csv = "a,b,c,d\n1,2,3,4"
    with pytest.raises(ValueError) as exc:
        parse_csv_loads(csv)
    assert "CSV header must be exactly" in str(exc.value)


def test_normalize_load_rows_to_scenario_text():
    rows = ["(1.0, 2.0), (3.0, 4.0)", "(2.0, 1.0), (4.0, 3.0)"]
    text = normalize_load_rows_to_scenario_text(rows)
    assert text == "(1.0, 2.0), (3.0, 4.0)\n(2.0, 1.0), (4.0, 3.0)\n"
def test_parse_numbered_tuple_loads_valid():
    txt = """loadNumber pickup dropoff\n1 (1.0, 2.0) (3.0, 4.0)\n2 (2.0, 1.0) (4.0, 3.0)\n"""
    rows = parse_txt_loads(txt)
    assert rows == ["(1.0, 2.0), (3.0, 4.0)", "(2.0, 1.0), (4.0, 3.0)"]

def test_parse_numbered_tuple_loads_no_header():
    txt = """1 (5.0, 6.0) (7.0, 8.0)\n2 (9.0, 10.0) (11.0, 12.0)\n"""
    rows = parse_txt_loads(txt)
    assert rows == ["(5.0, 6.0), (7.0, 8.0)", "(9.0, 10.0), (11.0, 12.0)"]
