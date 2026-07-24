from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SolverProgress:
    """Light‑weight snapshot emitted after each successful discharge iteration.

    Attributes:
        iteration: Current iteration number (starting at 1).
        current_driver_count: Number of active drivers after the discharge.
        current_total_time: Sum of driver route times after the discharge.
        current_max_driver_time: Maximum driver time after the discharge.
        applied_path: The min_path that was just applied (list of node IDs) or None.
        message: Optional diagnostic message.
        solver_phase: Structural routing-engine phase that produced the augmentation.
        augmentation_runtime_seconds: Runtime of the successful augmentation.
        cumulative_solver_runtime_seconds: Solver elapsed time at completion.
    """
    iteration: int
    current_driver_count: int
    current_total_time: float
    current_max_driver_time: float
    applied_path: Optional[List[int]]
    message: str = ""
    solver_phase: str | None = None
    augmentation_runtime_seconds: float | None = None
    cumulative_solver_runtime_seconds: float | None = None
