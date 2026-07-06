import re
import csv
import io
from pathlib import Path
import tempfile
from typing import List

# Regular expression for a single load row in the existing TXT format:
#   (pickup_x, pickup_y), (dropoff_x, dropoff_y)
#   Allows optional whitespace and supports floating point numbers (including negatives).
_TXT_ROW_REGEX = re.compile(
    r"^\s*\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)\s*,\s*\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)\s*$"
)


def _parse_numeric(val: str) -> float:
    """Convert a string to float, raising ValueError on failure."""
    try:
        return float(val)
    except ValueError as exc:
        raise ValueError(f"Invalid numeric value: {val!r}") from exc

def _parse_numbered_tuple_line(line: str) -> str:
    """Parse a numbered tuple row like "1 (x1, y1) (x2, y2)".

    Returns the legacy format string.
    """
    # Regex captures optional spaces, load number, and two coordinate tuples
    pattern = re.compile(
        r"^\s*(\d+)\s*\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)\s*"
        r"\(\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*,\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*\)\s*$"
    )
    m = pattern.match(line)
    if not m:
        raise ValueError("Line does not match numbered tuple table format.")
    # groups: 1=number, 2=px, 3=py, 4=dx, 5=dy
    px, py, dx, dy = map(_parse_numeric, m.group(2, 3, 4, 5))
    return f"({px}, {py}), ({dx}, {dy})"
def parse_txt_loads(text: str) -> List[str]:
    """Parse scenario text from user input.

    Supports:
    - Legacy format ``(x, y), (x, y)`` one per line.
    - Optional header line containing letters (e.g., "loadNumber pickup dropoff") which is ignored.
    - Numbered tuple table format: ``1 (x1, y1) (x2, y2)`` (load number column optional).

    Returns a list of rows in the legacy format.
    Raises ``ValueError`` on the first malformed line.
    """
    rows: List[str] = []
    header_skipped = False
    for i, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        # Skip a header line if it looks like a column header (e.g., contains 'loadNumber' or 'pickup'/'dropoff')
        if not header_skipped and re.search(r"(load\s*number|pickup|dropoff)", line, re.IGNORECASE):
            header_skipped = True
            continue
        # Legacy format
        if _TXT_ROW_REGEX.match(line):
            rows.append(line)
            continue
        # Numbered tuple format
        try:
            rows.append(_parse_numbered_tuple_line(line))
        except ValueError:
            raise ValueError(
                f"Line {i} does not match the required format."
            )
    if not rows:
        raise ValueError("No load rows found in the provided text.")
    return rows


def parse_csv_loads(text: str) -> List[str]:
    """Parse CSV scenario text.

    Expected header (case‑insensitive, spaces ignored):
        pickup_x,pickup_y,dropoff_x,dropoff_y
    Each subsequent row must contain exactly four numeric fields.
    Returns a list of rows formatted as the legacy TXT style.
    """
    csv_file = io.StringIO(text)
    reader = csv.reader(csv_file)
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("CSV file is empty.")

    normalized_header = [h.strip().lower() for h in header]
    expected = ["pickup_x", "pickup_y", "dropoff_x", "dropoff_y"]
    if normalized_header != expected:
        raise ValueError(
            f"CSV header must be exactly: {', '.join(expected)} (found: {', '.join(header)})"
        )

    rows: List[str] = []
    for i, row in enumerate(reader, start=2):
        if not row:
            continue
        if len(row) != 4:
            raise ValueError(f"Line {i}: expected 4 comma‑separated values, got {len(row)}.")
        try:
            nums = [_parse_numeric(v.strip()) for v in row]
        except ValueError as exc:
            raise ValueError(f"Line {i}: {exc}") from exc
        txt_row = f"({nums[0]}, {nums[1]}), ({nums[2]}, {nums[3]})"
        rows.append(txt_row)
    if not rows:
        raise ValueError("CSV file contains no data rows.")
    return rows


def normalize_load_rows_to_scenario_text(rows: List[str]) -> str:
    """Join validated rows into the final scenario file content.
    The legacy workflow expects one row per line.
    """
    return "\n".join(rows) + "\n"


def write_temp_scenario_file(text: str) -> Path:
    """Write ``text`` to a temporary ``.txt`` file and return its Path.
    Caller should delete the file after use.
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as tmp:
        tmp.write(text)
        return Path(tmp.name)
