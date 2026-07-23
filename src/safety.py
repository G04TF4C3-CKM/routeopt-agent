"""Local safety checks for the RouteOpt Agent workbench."""
from __future__ import annotations

from pathlib import Path


def assert_local_readable_file(file_path: str | Path) -> Path:
    """Reject URLs and non-readable paths; this backend is intentionally local-only."""
    raw = str(file_path)
    if "://" in raw:
        raise ValueError("Remote URLs are not accepted. Provide a local scenario file.")
    path = Path(file_path).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Not a readable local file: {path}")
    return path
