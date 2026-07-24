"""Stable wrapper around the legacy VRP optimization experiment."""
from __future__ import annotations

import contextlib
import io
import math
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional

from . import legacy_vrp as vrp
from .experimental_karp_mmc import discharge_mmc as karp_discharge
from .safety import assert_local_readable_file
from .scenario_loader import validate_scenario
from .solver_types import SolverProgress


def _monotonic_time() -> float:
    """Return a high-resolution monotonic timestamp for runtime diagnostics."""
    return time.perf_counter()


def _elapsed_seconds(start: float, end: float, *, label: str) -> float:
    """Return a validated elapsed interval from the routing-engine clock."""
    elapsed = float(end) - float(start)
    if not math.isfinite(elapsed) or elapsed < 0.0:
        raise RuntimeError(
            f"{label} must be finite and nonnegative; "
            "the routing-engine monotonic clock is inconsistent."
        )
    return elapsed


def _validated_runtime(value: float, *, label: str) -> float:
    """Reject invalid accumulated timing values rather than hiding them."""
    runtime = float(value)
    if not math.isfinite(runtime) or runtime < 0.0:
        raise RuntimeError(f"{label} must be finite and nonnegative.")
    return runtime


def _driver_total_time(drivers: vrp.Drivers) -> float:
    return float(sum(drivers.time.values()))


def _driver_count(drivers: vrp.Drivers) -> int:
    return int(len(drivers.labels))


def _routes_as_lists(drivers: vrp.Drivers) -> Dict[str, List[int]]:
    return {str(k): [int(v) for v in route] for k, route in sorted(drivers.sched.items())}


def solve_routing_problem(
    file_path: str | Path,
    time_limit: float = 12.0,
    max_iterations: int = 50,
    strength: str = "strong",
    residual_type: str = "mod",
    suppress_legacy_output: bool = True,
    *,
    solver_mode: str = "bellman_discharge",
    progress_callback: Callable[[SolverProgress], None] | None = None,
) -> Dict[str, Any]:
    """Solve a local vehicle-routing scenario using the legacy optimizer.

    The legacy solver starts with one driver per load and repeatedly applies feasible
    residual-graph discharges to combine routes while respecting the driver time limit.
    """
    routing_engine_start = _monotonic_time()
    path = assert_local_readable_file(file_path)
    validation = validate_scenario(path)
    # Validate solver mode (support bellman_discharge and karp_mmc)
    if solver_mode not in ("bellman_discharge", "karp_mmc"):
        raise ValueError(f"Unsupported solver_mode: {solver_mode}")

    def _run() -> Dict[str, Any]:
        graph = vrp.create_graph_from_file(str(path))
        drivers = vrp.Drivers(graph, time_limit=time_limit, res_type=residual_type, wp=False)

        initial_driver_count = _driver_count(drivers)
        initial_total_time = _driver_total_time(drivers)
        initial_routes = _routes_as_lists(drivers)

        iterations = 0
        applied_paths: List[List[int]] = []
        augmentation_records: List[Dict[str, Any]] = []
        last_cycle: Optional[List[int]] = None
        min_path: Optional[List[int]] = []
        progress_callback_runtime_seconds = 0.0
        final_success_boundary: float | None = None

        def _record_successful_augmentation(
            *,
            iteration: int,
            solver_phase: str,
            applied_path: List[int],
            message: str,
            attempt_start: float,
        ) -> None:
            nonlocal final_success_boundary
            nonlocal progress_callback_runtime_seconds

            current_driver_count = _driver_count(drivers)
            current_total_time = _driver_total_time(drivers)
            current_max_driver_time = (
                float(max(drivers.time.values())) if drivers.time else 0.0
            )
            augmentation_completion = _monotonic_time()
            augmentation_runtime_seconds = _elapsed_seconds(
                attempt_start,
                augmentation_completion,
                label="augmentation runtime",
            )
            cumulative_solver_runtime_seconds = _elapsed_seconds(
                solver_phase_start,
                augmentation_completion,
                label="cumulative solver runtime",
            )

            augmentation_records.append(
                {
                    "iteration": int(iteration),
                    "solver_phase": solver_phase,
                    "applied_path": list(applied_path),
                    "current_driver_count": current_driver_count,
                    "current_total_time": current_total_time,
                    "current_max_driver_time": current_max_driver_time,
                    "augmentation_runtime_seconds": augmentation_runtime_seconds,
                    "cumulative_solver_runtime_seconds": (
                        cumulative_solver_runtime_seconds
                    ),
                    "message": message,
                }
            )
            progress = SolverProgress(
                iteration=iteration,
                current_driver_count=current_driver_count,
                current_total_time=current_total_time,
                current_max_driver_time=current_max_driver_time,
                applied_path=list(applied_path),
                message=message,
                solver_phase=solver_phase,
                augmentation_runtime_seconds=augmentation_runtime_seconds,
                cumulative_solver_runtime_seconds=(
                    cumulative_solver_runtime_seconds
                ),
            )

            if progress_callback is not None:
                callback_start = _monotonic_time()
                progress_callback(progress)
                callback_end = _monotonic_time()
                callback_runtime = _elapsed_seconds(
                    callback_start,
                    callback_end,
                    label="progress callback runtime",
                )
                progress_callback_runtime_seconds = _validated_runtime(
                    progress_callback_runtime_seconds + callback_runtime,
                    label="accumulated progress callback runtime",
                )
                final_success_boundary = callback_end
            else:
                final_success_boundary = _monotonic_time()

        solver_phase_start = _monotonic_time()
        problem_setup_runtime_seconds = _elapsed_seconds(
            routing_engine_start,
            solver_phase_start,
            label="problem setup runtime",
        )

        if solver_mode == "bellman_discharge":
            # existing Bellman‑Ford discharge loop
            while min_path is not None and iterations < max_iterations:
                iterations += 1
                attempt_start = _monotonic_time()
                min_path, cycle = vrp.discharge_bellmanford(
                    drivers,
                    time_limit=time_limit,
                    relax_limit=None,
                    strength=strength,
                    wp=False,
                )
                if min_path is not None:
                    applied_path = [int(x) for x in min_path]
                    applied_paths.append(applied_path)
                    _record_successful_augmentation(
                        iteration=iterations,
                        solver_phase="bellman_firing_path",
                        applied_path=applied_path,
                        message="discharge applied",
                        attempt_start=attempt_start,
                    )
                # remember last cycle (may be None)
                last_cycle = cycle
        else:
            # experimental Karp/MMC mode
            while iterations < max_iterations:
                attempt_start = _monotonic_time()
                firing_path = karp_discharge(drivers, wp=False, version=1)
                if firing_path is None:
                    break
                applied_path = [int(x) for x in firing_path]
                applied_paths.append(applied_path)
                last_cycle = firing_path
                iterations += 1
                _record_successful_augmentation(
                    iteration=iterations,
                    solver_phase="karp_mmc_v1_firing_path",
                    applied_path=applied_path,
                    message="karp/mmc firing path applied",
                    attempt_start=attempt_start,
                )

            # Apply at most one source-rooted version-2 augmentation: repeated
            # discharge can yield unresolved compound walks with embedded central cycles.
            if iterations < max_iterations:
                attempt_start = _monotonic_time()
                source_rooted_cycle = karp_discharge(drivers, wp=False, version=2)
                if source_rooted_cycle is not None:
                    applied_path = [int(x) for x in source_rooted_cycle]
                    applied_paths.append(applied_path)
                    last_cycle = source_rooted_cycle
                    iterations += 1
                    _record_successful_augmentation(
                        iteration=iterations,
                        solver_phase="karp_mmc_v2_source_rooted_cycle",
                        applied_path=applied_path,
                        message="karp/mmc source-rooted cycle applied",
                        attempt_start=attempt_start,
                    )

        solver_end = _monotonic_time()
        solver_runtime_seconds = _elapsed_seconds(
            solver_phase_start,
            solver_end,
            label="solver runtime",
        )
        termination_tail_runtime_seconds = (
            solver_runtime_seconds
            if final_success_boundary is None
            else _elapsed_seconds(
                final_success_boundary,
                solver_end,
                label="termination tail runtime",
            )
        )

        final_total_time = _driver_total_time(drivers)
        max_driver_time = float(max(drivers.time.values())) if drivers.time else 0.0
        feasible = bool(not drivers.hot_drivers and max_driver_time <= time_limit)
        result = {
            "scenario_path": str(path),
            "load_count": validation["load_count"],
            "time_limit": float(time_limit),
            "iterations": iterations,
            "terminated_by_iteration_limit": iterations >= max_iterations and (
                (solver_mode == "bellman_discharge" and min_path is not None) or
                solver_mode == "karp_mmc"
            ),
            "negative_cycle": last_cycle,
            "initial_driver_count": initial_driver_count,
            "final_driver_count": _driver_count(drivers),
            "initial_total_time": initial_total_time,
            "final_total_time": final_total_time,
            "max_driver_time": max_driver_time,
            "feasible": feasible,
            "initial_routes": initial_routes,
            "routes": _routes_as_lists(drivers),
            "applied_paths": applied_paths,
            "augmentation_records": augmentation_records,
            "validation": validation,
        }
        routing_engine_end = _monotonic_time()
        result["timing"] = {
            "routing_engine_runtime_seconds": _elapsed_seconds(
                routing_engine_start,
                routing_engine_end,
                label="routing-engine runtime",
            ),
            "problem_setup_runtime_seconds": problem_setup_runtime_seconds,
            "solver_runtime_seconds": solver_runtime_seconds,
            "progress_callback_runtime_seconds": _validated_runtime(
                progress_callback_runtime_seconds,
                label="progress callback runtime",
            ),
            "termination_tail_runtime_seconds": (
                termination_tail_runtime_seconds
            ),
            "result_finalization_runtime_seconds": _elapsed_seconds(
                solver_end,
                routing_engine_end,
                label="result finalization runtime",
            ),
        }
        return result

    if suppress_legacy_output:
        with contextlib.redirect_stdout(io.StringIO()):
            return _run()
    return _run()
