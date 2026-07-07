from pathlib import Path

import pytest

from src.routing_engine import solve_routing_problem
from src.solver_types import SolverProgress

SAMPLE = Path("data/sample_8_loads.txt")


def test_default_solver_behavior_is_preserved():
    result = solve_routing_problem(SAMPLE, time_limit=12.0)

    assert result["final_driver_count"] == 3
    assert result["feasible"] is True


def test_explicit_bellman_discharge_mode_matches_default():
    default = solve_routing_problem(SAMPLE, time_limit=12.0)
    explicit = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        solver_mode="bellman_discharge",
    )

    assert explicit["final_driver_count"] == default["final_driver_count"]
    assert explicit["final_total_time"] == default["final_total_time"]
    assert explicit["feasible"] == default["feasible"]


def test_unsupported_solver_mode_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported solver_mode"):
        solve_routing_problem(SAMPLE, time_limit=12.0, solver_mode="not_a_solver")


def test_progress_callback_none_preserves_behavior():
    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        progress_callback=None,
    )

    assert result["final_driver_count"] == 3
    assert result["feasible"] is True


def test_progress_callback_is_invoked():
    calls: list[SolverProgress] = []

    def callback(progress: SolverProgress) -> None:
        calls.append(progress)

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=10,
        progress_callback=callback,
    )

    assert result["iterations"] >= 1
    assert calls
    assert isinstance(calls[0], SolverProgress)
    assert calls[0].iteration >= 1
    assert calls[0].current_driver_count > 0
    assert calls[0].current_total_time > 0
    assert calls[0].current_max_driver_time > 0


def test_max_iterations_limit_is_respected():
    result = solve_routing_problem(SAMPLE, time_limit=12.0, max_iterations=1)

    assert result["iterations"] <= 1


def test_karp_mmc_solver_mode_is_accepted():
    result = solve_routing_problem(SAMPLE, time_limit=12.0, solver_mode="karp_mmc")
    assert isinstance(result, dict)
    assert result["final_driver_count"] == 8
    assert result["feasible"] is True
    assert result["applied_paths"] == []
