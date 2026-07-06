"""Convert routing-engine output into business-readable metrics and summaries."""
from __future__ import annotations

from typing import Dict, Any


def analyze_solution(result: Dict[str, Any]) -> Dict[str, Any]:
    """Compute derived metrics from a routing solution."""
    initial = result["initial_driver_count"]
    final = result["final_driver_count"]
    initial_time = result["initial_total_time"]
    final_time = result["final_total_time"]
    return {
        "drivers_saved": initial - final,
        "driver_reduction_pct": 0.0 if initial == 0 else 100.0 * (initial - final) / initial,
        "total_time_saved": initial_time - final_time,
        "total_time_reduction_pct": 0.0 if initial_time == 0 else 100.0 * (initial_time - final_time) / initial_time,
        "is_feasible": result["feasible"],
    }


def explain_solution(result: Dict[str, Any]) -> str:
    """Create a concise user-facing explanation of the routing result."""
    analysis = analyze_solution(result)
    feasibility = "feasible" if analysis["is_feasible"] else "not feasible"
    return (
        f"The optimizer reduced the plan from {result['initial_driver_count']} drivers "
        f"to {result['final_driver_count']} drivers, saving {analysis['drivers_saved']} drivers "
        f"({analysis['driver_reduction_pct']:.1f}% reduction). Total route time changed from "
        f"{result['initial_total_time']:.3f} to {result['final_total_time']:.3f}, a savings of "
        f"{analysis['total_time_saved']:.3f} time units. The final maximum driver time is "
        f"{result['max_driver_time']:.3f} against a limit of {result['time_limit']:.3f}, so the "
        f"solution is {feasibility}."
    )
