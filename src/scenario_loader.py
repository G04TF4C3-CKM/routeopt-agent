"""Utilities for loading and validating simple vehicle-routing scenarios."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

Coordinate = Tuple[float, float]
Load = Tuple[Coordinate, Coordinate]

_LOAD_PATTERN = re.compile(
    r"^\s*\(?\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*\)?\s*,\s*"
    r"\(?\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*\)?\s*$"
)


def parse_load_line(line: str) -> Load:
    """Parse one line of the form ``(px, py), (dx, dy)``."""
    match = _LOAD_PATTERN.match(line.strip())
    if not match:
        raise ValueError(f"Invalid load line: {line!r}")
    px, py, dx, dy = map(float, match.groups())
    return (px, py), (dx, dy)


def load_scenario(file_path: str | Path) -> List[Load]:
    """Load a scenario file into pickup/dropoff coordinate pairs."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {path}")
    loads: List[Load] = []
    for line_number, raw_line in enumerate(path.read_text().splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            loads.append(parse_load_line(line))
        except ValueError as exc:
            raise ValueError(f"{exc} at line {line_number}") from exc
    if not loads:
        raise ValueError(f"Scenario file contains no loads: {path}")
    return loads


def validate_scenario(file_path: str | Path, max_loads: int = 128) -> dict:
    """Return a simple validation report for a local scenario file."""
    path = Path(file_path)
    loads = load_scenario(path)
    warnings = []
    if len(loads) > max_loads:
        raise ValueError(f"Scenario has {len(loads)} loads; maximum allowed is {max_loads}.")
    if path.suffix.lower() not in {".txt", ".csv", ""}:
        warnings.append(f"Unexpected file extension {path.suffix!r}; expected .txt or .csv.")
    return {"valid": True, "load_count": len(loads), "warnings": warnings}
