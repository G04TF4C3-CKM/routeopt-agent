"""Minimal agent-style workflow for the routing capstone.

This intentionally keeps the backend deterministic. A later UI/LLM layer can call this
workflow and narrate its output, but the solver itself remains testable and local-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .result_analyzer import analyze_solution, explain_solution
from .routing_engine import solve_routing_problem
from .scenario_loader import validate_scenario
from .safety import assert_local_readable_file


@dataclass
class WorkflowState:
    scenario_path: str
    time_limit: float = 12.0
    valid: bool = False
    errors: List[str] = field(default_factory=list)
    validation: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    analysis: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None


def load_scenario_node(state: WorkflowState) -> WorkflowState:
    state.scenario_path = str(assert_local_readable_file(state.scenario_path))
    return state


def validate_scenario_node(state: WorkflowState) -> WorkflowState:
    state.validation = validate_scenario(Path(state.scenario_path))
    state.valid = state.validation["valid"]
    return state


def run_optimizer_node(state: WorkflowState) -> WorkflowState:
    state.result = solve_routing_problem(state.scenario_path, time_limit=state.time_limit)
    return state


def analyze_solution_node(state: WorkflowState) -> WorkflowState:
    if state.result is None:
        raise ValueError("Cannot analyze solution before optimizer runs.")
    state.analysis = analyze_solution(state.result)
    return state


def explain_solution_node(state: WorkflowState) -> WorkflowState:
    if state.result is None:
        raise ValueError("Cannot explain solution before optimizer runs.")
    state.explanation = explain_solution(state.result)
    return state


def run_routing_workflow(scenario_path: str | Path, time_limit: float = 12.0) -> WorkflowState:
    """Run the capstone graph workflow: load → validate → optimize → analyze → explain."""
    state = WorkflowState(scenario_path=str(scenario_path), time_limit=time_limit)
    try:
        for node in (
            load_scenario_node,
            validate_scenario_node,
            run_optimizer_node,
            analyze_solution_node,
            explain_solution_node,
        ):
            state = node(state)
    except Exception as exc:  # Convert exceptions to workflow state for UI display.
        state.errors.append(str(exc))
    return state
