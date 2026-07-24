"""Red Team regressions for backend and per-augmentation timing diagnostics."""

from __future__ import annotations

from collections.abc import Callable
import math
from pathlib import Path
from typing import Any

import pytest

from src import routing_engine
from src.routing_engine import solve_routing_problem
from src.solver_types import SolverProgress


SAMPLE = Path("data/sample_8_loads.txt")
HISTORICAL_FIXTURE = (
    Path(__file__).parent / "fixtures" / "loads_5_8_hiring_firing_path.txt"
)
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

CLOCK_SEAM_NAME = "_monotonic_time"
CLOCK_SEAM = getattr(routing_engine, CLOCK_SEAM_NAME, None)
requires_clock_seam = pytest.mark.skipif(
    not callable(CLOCK_SEAM),
    reason="src.routing_engine._monotonic_time has not been implemented yet",
)

TIMING_FIELDS = {
    "routing_engine_runtime_seconds",
    "problem_setup_runtime_seconds",
    "solver_runtime_seconds",
    "progress_callback_runtime_seconds",
    "termination_tail_runtime_seconds",
    "result_finalization_runtime_seconds",
}
AUGMENTATION_FIELDS = {
    "iteration",
    "solver_phase",
    "applied_path",
    "current_driver_count",
    "current_total_time",
    "current_max_driver_time",
    "augmentation_runtime_seconds",
    "cumulative_solver_runtime_seconds",
    "message",
}
TIMING_TOLERANCE = 1e-9


class ManualClock:
    """Monotonic clock advanced only by explicit test-controlled operations."""

    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        assert seconds >= 0
        self.value += seconds


def _install_clock(monkeypatch: pytest.MonkeyPatch, clock: ManualClock) -> None:
    monkeypatch.setattr(routing_engine, CLOCK_SEAM_NAME, clock)


def _timing(result: dict[str, Any]) -> dict[str, float]:
    timing = result.get("timing")
    assert isinstance(timing, dict), (
        "Normalized solver results must expose the backend timing contract."
    )
    assert set(timing) == TIMING_FIELDS
    return timing


def _augmentation_records(result: dict[str, Any]) -> list[dict[str, Any]]:
    records = result.get("augmentation_records")
    assert isinstance(records, list), (
        "Normalized solver results must retain augmentation records even when "
        "no progress callback was supplied."
    )
    assert all(isinstance(record, dict) for record in records)
    assert all(AUGMENTATION_FIELDS <= set(record) for record in records)
    return records


def _assert_finite_nonnegative(value: Any) -> None:
    assert isinstance(value, (int, float))
    assert math.isfinite(float(value))
    assert float(value) >= 0.0


def _assert_timing_reconciliation(result: dict[str, Any]) -> None:
    timing = _timing(result)
    records = _augmentation_records(result)

    for value in timing.values():
        _assert_finite_nonnegative(value)
    for record in records:
        _assert_finite_nonnegative(record["augmentation_runtime_seconds"])
        _assert_finite_nonnegative(record["cumulative_solver_runtime_seconds"])

    routing_engine_remainder = (
        timing["routing_engine_runtime_seconds"]
        - timing["problem_setup_runtime_seconds"]
        - timing["solver_runtime_seconds"]
        - timing["result_finalization_runtime_seconds"]
    )
    solver_bookkeeping_remainder = (
        timing["solver_runtime_seconds"]
        - sum(
            float(record["augmentation_runtime_seconds"]) for record in records
        )
        - timing["progress_callback_runtime_seconds"]
        - timing["termination_tail_runtime_seconds"]
    )
    assert routing_engine_remainder >= -TIMING_TOLERANCE
    assert solver_bookkeeping_remainder >= -TIMING_TOLERANCE


def _wrap_real_bellman_attempts(
    monkeypatch: pytest.MonkeyPatch,
    clock: ManualClock,
    durations: list[float],
) -> list[tuple[list[int] | None, list[int] | None]]:
    original = routing_engine.vrp.discharge_bellmanford
    remaining = list(durations)
    attempts: list[tuple[list[int] | None, list[int] | None]] = []

    def wrapped(*args: Any, **kwargs: Any):
        if not remaining:
            pytest.fail("Bellman-Ford made more attempts than the test clock expected.")
        result = original(*args, **kwargs)
        clock.advance(remaining.pop(0))
        attempts.append(result)
        return result

    monkeypatch.setattr(routing_engine.vrp, "discharge_bellmanford", wrapped)
    return attempts


def _wrap_real_karp_attempts(
    monkeypatch: pytest.MonkeyPatch,
    clock: ManualClock,
    duration_for_result: Callable[[int | None, list[int] | None], float],
) -> list[tuple[int | None, list[int] | None]]:
    original = routing_engine.karp_discharge
    attempts: list[tuple[int | None, list[int] | None]] = []

    def wrapped(
        drivers: Any,
        wp: bool = False,
        version: int | None = None,
    ):
        result = original(drivers, wp=wp, version=version)
        clock.advance(duration_for_result(version, result))
        attempts.append((version, result))
        return result

    monkeypatch.setattr(routing_engine, "karp_discharge", wrapped)
    return attempts


def test_routing_engine_exposes_monkeypatchable_monotonic_clock_seam() -> None:
    assert callable(CLOCK_SEAM), (
        "src.routing_engine must expose a module-level _monotonic_time callable "
        "wrapping a monotonic clock such as time.perf_counter()."
    )


def test_solver_progress_retains_original_constructor_with_optional_timing() -> None:
    progress = SolverProgress(
        iteration=1,
        current_driver_count=2,
        current_total_time=18.0,
        current_max_driver_time=10.0,
        applied_path=[-1, 2, 1, 0],
        message="discharge applied",
    )

    assert hasattr(progress, "solver_phase")
    assert hasattr(progress, "augmentation_runtime_seconds")
    assert hasattr(progress, "cumulative_solver_runtime_seconds")
    assert progress.solver_phase is None
    assert progress.augmentation_runtime_seconds is None
    assert progress.cumulative_solver_runtime_seconds is None


def test_normalized_result_exposes_timing_and_callback_independent_records() -> None:
    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=1,
        progress_callback=None,
    )

    timing = _timing(result)
    records = _augmentation_records(result)

    assert timing["progress_callback_runtime_seconds"] == pytest.approx(0.0)
    assert records
    assert [record["applied_path"] for record in records] == result["applied_paths"]


@requires_clock_seam
def test_bellman_successful_augmentation_has_exact_synthetic_duration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    attempts = _wrap_real_bellman_attempts(monkeypatch, clock, [1.25])

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=1,
        progress_callback=None,
    )
    records = _augmentation_records(result)

    assert len(attempts) == 1
    assert len(records) == 1
    assert records[0]["solver_phase"] == "bellman_firing_path"
    assert records[0]["augmentation_runtime_seconds"] == pytest.approx(1.25)
    assert records[0]["cumulative_solver_runtime_seconds"] == pytest.approx(1.25)
    assert _timing(result)["progress_callback_runtime_seconds"] == pytest.approx(0.0)


@requires_clock_seam
def test_bellman_augmentations_have_independent_monotone_durations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    _wrap_real_bellman_attempts(monkeypatch, clock, [0.75, 1.5])

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=2,
        progress_callback=None,
    )
    records = _augmentation_records(result)

    assert [record["augmentation_runtime_seconds"] for record in records] == pytest.approx(
        [0.75, 1.5]
    )
    cumulative = [
        float(record["cumulative_solver_runtime_seconds"]) for record in records
    ]
    assert cumulative == pytest.approx([0.75, 2.25])
    assert cumulative == sorted(cumulative)


@requires_clock_seam
def test_bellman_final_unsuccessful_search_is_in_termination_tail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    original = routing_engine.vrp.discharge_bellmanford
    call_count = 0

    def one_success_then_stop(*args: Any, **kwargs: Any):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            result = original(*args, **kwargs)
            clock.advance(1.0)
            assert result[0] is not None
            return result
        clock.advance(3.0)
        return None, None

    monkeypatch.setattr(
        routing_engine.vrp,
        "discharge_bellmanford",
        one_success_then_stop,
    )

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=10,
        progress_callback=None,
    )
    timing = _timing(result)

    assert call_count == 2
    assert len(_augmentation_records(result)) == 1
    assert timing["solver_runtime_seconds"] == pytest.approx(4.0)
    assert timing["termination_tail_runtime_seconds"] == pytest.approx(3.0)


@requires_clock_seam
def test_bellman_iteration_limit_does_not_fabricate_unsuccessful_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    attempts = _wrap_real_bellman_attempts(monkeypatch, clock, [1.0])

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=1,
        progress_callback=None,
    )

    assert len(attempts) == 1
    assert result["terminated_by_iteration_limit"] is True
    assert len(_augmentation_records(result)) == 1
    assert _timing(result)["termination_tail_runtime_seconds"] == pytest.approx(0.0)


@requires_clock_seam
def test_zero_success_assigns_complete_solver_phase_to_termination_tail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)

    def unsuccessful_attempt(*args: Any, **kwargs: Any):
        clock.advance(4.0)
        return None, None

    monkeypatch.setattr(
        routing_engine.vrp,
        "discharge_bellmanford",
        unsuccessful_attempt,
    )

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=10,
        progress_callback=None,
    )
    timing = _timing(result)

    assert _augmentation_records(result) == []
    assert timing["solver_runtime_seconds"] == pytest.approx(4.0)
    assert timing["termination_tail_runtime_seconds"] == pytest.approx(
        timing["solver_runtime_seconds"]
    )


@requires_clock_seam
def test_karp_v1_uses_common_successful_augmentation_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    attempts = _wrap_real_karp_attempts(
        monkeypatch,
        clock,
        lambda version, result: 1.75,
    )

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        solver_mode="karp_mmc",
        max_iterations=1,
        progress_callback=None,
    )
    records = _augmentation_records(result)

    assert attempts and attempts[0][0] == 1
    assert len(records) == 1
    assert records[0]["solver_phase"] == "karp_mmc_v1_firing_path"
    assert records[0]["augmentation_runtime_seconds"] == pytest.approx(1.75)
    assert records[0]["cumulative_solver_runtime_seconds"] == pytest.approx(1.75)


@requires_clock_seam
def test_karp_failed_v1_search_is_not_charged_to_successful_v2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)

    def duration(version: int | None, result: list[int] | None) -> float:
        if version == 2:
            return 2.0
        return 5.0 if result is None else 0.5

    attempts = _wrap_real_karp_attempts(monkeypatch, clock, duration)
    result = solve_routing_problem(
        HISTORICAL_FIXTURE,
        time_limit=12.0,
        solver_mode="karp_mmc",
        max_iterations=20,
        progress_callback=None,
    )
    records = _augmentation_records(result)
    last_record = records[-1]

    assert any(version == 1 and walk is None for version, walk in attempts)
    assert attempts[-1][0] == 2
    assert attempts[-1][1] is not None
    assert last_record["solver_phase"] == "karp_mmc_v2_source_rooted_cycle"
    assert last_record["augmentation_runtime_seconds"] == pytest.approx(2.0)
    assert (
        last_record["cumulative_solver_runtime_seconds"]
        - records[-2]["cumulative_solver_runtime_seconds"]
    ) == pytest.approx(7.0)

    solver_remainder = (
        _timing(result)["solver_runtime_seconds"]
        - sum(record["augmentation_runtime_seconds"] for record in records)
        - _timing(result)["progress_callback_runtime_seconds"]
        - _timing(result)["termination_tail_runtime_seconds"]
    )
    assert solver_remainder == pytest.approx(5.0)


@requires_clock_seam
def test_callback_runtime_is_separate_from_augmentation_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    _wrap_real_bellman_attempts(monkeypatch, clock, [1.0, 2.0])
    events: list[SolverProgress] = []

    def callback(progress: SolverProgress) -> None:
        events.append(progress)
        clock.advance(0.5)

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=2,
        progress_callback=callback,
    )
    timing = _timing(result)
    records = _augmentation_records(result)

    assert [record["augmentation_runtime_seconds"] for record in records] == pytest.approx(
        [1.0, 2.0]
    )
    assert timing["progress_callback_runtime_seconds"] == pytest.approx(1.0)
    assert timing["solver_runtime_seconds"] == pytest.approx(4.0)
    assert [
        record["cumulative_solver_runtime_seconds"] for record in records
    ] == pytest.approx([1.0, 3.5])
    assert [event.solver_phase for event in events] == [
        "bellman_firing_path",
        "bellman_firing_path",
    ]
    assert [
        event.augmentation_runtime_seconds for event in events
    ] == pytest.approx([1.0, 2.0])


@requires_clock_seam
def test_termination_tail_starts_after_final_callback_returns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    original = routing_engine.vrp.discharge_bellmanford
    call_count = 0

    def one_success_then_stop(*args: Any, **kwargs: Any):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            result = original(*args, **kwargs)
            clock.advance(1.0)
            return result
        clock.advance(3.0)
        return None, None

    def callback(progress: SolverProgress) -> None:
        clock.advance(2.0)

    monkeypatch.setattr(
        routing_engine.vrp,
        "discharge_bellmanford",
        one_success_then_stop,
    )
    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        max_iterations=10,
        progress_callback=callback,
    )
    timing = _timing(result)

    assert timing["solver_runtime_seconds"] == pytest.approx(6.0)
    assert timing["progress_callback_runtime_seconds"] == pytest.approx(2.0)
    assert timing["termination_tail_runtime_seconds"] == pytest.approx(3.0)


@requires_clock_seam
@pytest.mark.parametrize(
    ("solver_mode", "scenario", "max_iterations"),
    (
        ("bellman_discharge", SAMPLE, 50),
        ("karp_mmc", HISTORICAL_FIXTURE, 20),
    ),
)
def test_instrumentation_preserves_solver_outputs_and_historical_walks(
    monkeypatch: pytest.MonkeyPatch,
    solver_mode: str,
    scenario: Path,
    max_iterations: int,
) -> None:
    baseline = solve_routing_problem(
        scenario,
        time_limit=12.0,
        solver_mode=solver_mode,
        max_iterations=max_iterations,
        progress_callback=None,
    )

    clock = ManualClock()
    _install_clock(monkeypatch, clock)
    instrumented = solve_routing_problem(
        scenario,
        time_limit=12.0,
        solver_mode=solver_mode,
        max_iterations=max_iterations,
        progress_callback=None,
    )

    for key in (
        "applied_paths",
        "routes",
        "initial_driver_count",
        "final_driver_count",
        "final_total_time",
        "max_driver_time",
        "feasible",
    ):
        assert instrumented[key] == baseline[key]

    records = _augmentation_records(instrumented)
    assert [record["applied_path"] for record in records] == instrumented[
        "applied_paths"
    ]
    assert _timing(instrumented)["progress_callback_runtime_seconds"] == pytest.approx(
        0.0
    )

    if solver_mode == "karp_mmc":
        assert instrumented["applied_paths"][:3] == HISTORICAL_FIRING_PATHS
        assert HISTORICAL_RECONNECTION_CYCLE in instrumented["applied_paths"]


@requires_clock_seam
@pytest.mark.parametrize("solver_mode", ("bellman_discharge", "karp_mmc"))
def test_all_timing_values_are_finite_nonnegative_and_reconcile(
    monkeypatch: pytest.MonkeyPatch,
    solver_mode: str,
) -> None:
    clock = ManualClock()
    _install_clock(monkeypatch, clock)

    result = solve_routing_problem(
        SAMPLE,
        time_limit=12.0,
        solver_mode=solver_mode,
        max_iterations=2,
        progress_callback=None,
    )

    _assert_timing_reconciliation(result)
    records = _augmentation_records(result)
    cumulative = [
        float(record["cumulative_solver_runtime_seconds"]) for record in records
    ]
    assert cumulative == sorted(cumulative)
    assert [record["applied_path"] for record in records] == result["applied_paths"]
