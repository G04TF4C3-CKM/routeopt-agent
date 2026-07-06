"""Stable wrapper around the legacy VRP optimization experiment."""
from __future__ import annotations

import contextlib
import io
from pathlib import Path
from typing import Any, Dict, List

from . import legacy_vrp as vrp
from .safety import assert_local_readable_file
from .scenario_loader import validate_scenario


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
) -> Dict[str, Any]:
    """Solve a local vehicle-routing scenario using the legacy optimizer.

    The legacy solver starts with one driver per load and repeatedly applies feasible
    residual-graph discharges to combine routes while respecting the driver time limit.
    """
    path = assert_local_readable_file(file_path)
    validation = validate_scenario(path)

    def _run() -> Dict[str, Any]:
        graph = vrp.create_graph_from_file(str(path))
        drivers = vrp.Drivers(graph, time_limit=time_limit, res_type=residual_type, wp=False)

        initial_driver_count = _driver_count(drivers)
        initial_total_time = _driver_total_time(drivers)
        initial_routes = _routes_as_lists(drivers)

        iterations = 0
        min_path = []
        cycle = None
        applied_paths = []
        while min_path is not None and iterations < max_iterations:
            iterations += 1
            min_path, cycle = vrp.discharge_bellmanford(
                drivers,
                time_limit=time_limit,
                relax_limit=None,
                strength=strength,
                wp=False,
            )
            if min_path is not None:
                applied_paths.append([int(x) for x in min_path])

        final_total_time = _driver_total_time(drivers)
        max_driver_time = float(max(drivers.time.values())) if drivers.time else 0.0
        feasible = bool(not drivers.hot_drivers and max_driver_time <= time_limit)
        return {
            "scenario_path": str(path),
            "load_count": validation["load_count"],
            "time_limit": float(time_limit),
            "iterations": iterations,
            "terminated_by_iteration_limit": iterations >= max_iterations and min_path is not None,
            "negative_cycle": cycle,
            "initial_driver_count": initial_driver_count,
            "final_driver_count": _driver_count(drivers),
            "initial_total_time": initial_total_time,
            "final_total_time": final_total_time,
            "max_driver_time": max_driver_time,
            "feasible": feasible,
            "initial_routes": initial_routes,
            "routes": _routes_as_lists(drivers),
            "applied_paths": applied_paths,
            "validation": validation,
        }

    if suppress_legacy_output:
        with contextlib.redirect_stdout(io.StringIO()):
            return _run()
    return _run()
