from pathlib import Path

import pytest

from src.scenario_loader import load_scenario, parse_load_line, validate_scenario


def test_parse_load_line():
    assert parse_load_line("(1.0, 2.0), (3.0, 4.0)") == ((1.0, 2.0), (3.0, 4.0))


def test_load_sample_scenario():
    loads = load_scenario(Path("data/sample_8_loads.txt"))
    assert len(loads) == 8


def test_validate_empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("\n")
    with pytest.raises(ValueError):
        validate_scenario(p)
