"""Historical smoke test for the complete Karp/MMC behavior.

The expected values below come from the saved outputs in the original
``KarpsMeanMinCycle_2.ipynb`` and ``DoubleCheck_Optimality.ipynb`` notebooks.
The production Karp/MMC extraction is currently incomplete, so the behavioral
oracle is marked as a strict expected failure.  Once the port reproduces the
historical result, pytest will report XPASS as a failure and force us to remove
the marker deliberately.
"""

from pathlib import Path

import pytest

from src.routing_engine import solve_routing_problem


FIXTURE = Path(__file__).parent / "fixtures" / "loads_5_8_hiring_firing_path.txt"

HISTORICAL_FIRING_PATHS = [
    [-1, 10, 1, 0],
    [-1, 2, 7, 0],
    [-1, 4, 5, 0],
]

HISTORICAL_RECONNECTION_CYCLE = [
    0,
    5,
    4,
    1,
    10,
    7,
    2,
    -1,
    6,
    9,
    0,
]

HISTORICAL_FINAL_TOTAL_TIME = 21.677714866639274


def test_historical_fixture_is_present_and_has_five_loads() -> None:
    """Guard against losing or silently replacing the notebook fixture."""

    lines = [line for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert len(lines) == 5
    assert all(line.count("(") == 2 and line.count(")") == 2 for line in lines)


def test_historical_karp_mmc_smoke() -> None:
    """Reproduce the complete historical Karp/MMC solution on the diagnostic case."""

    result = solve_routing_problem(
        FIXTURE,
        time_limit=12.0,
        solver_mode="karp_mmc",
        max_iterations=20,
    )

    assert result["feasible"] is True
    assert result["initial_driver_count"] == 5
    assert result["final_driver_count"] == 2

    walks = result["applied_paths"]
    assert walks[:3] == HISTORICAL_FIRING_PATHS
    assert HISTORICAL_RECONNECTION_CYCLE in walks

    assert result["final_total_time"] == pytest.approx(
        HISTORICAL_FINAL_TOTAL_TIME,
        abs=1e-6,
    )
    assert result["max_driver_time"] <= 12.0
