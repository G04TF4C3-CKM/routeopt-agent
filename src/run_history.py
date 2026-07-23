"""Serializable run records and immutable session-history transitions."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Literal, Mapping, Sequence, TypeAlias, TypedDict, cast
import uuid

from .solver_types import SolverProgress


JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
ActiveView: TypeAlias = Literal["summary", "details"]


class ProgressEventRecord(TypedDict):
    iteration: int
    current_driver_count: int
    current_total_time: float
    current_max_driver_time: float
    applied_path: list[int] | None
    message: str


class ManagerSummary(TypedDict):
    initial_driver_count: int
    final_driver_count: int
    drivers_saved: int
    initial_total_time: float
    final_total_time: float
    total_time_saved: float
    max_driver_time: float
    feasible: bool


class RunRecord(TypedDict):
    schema_version: int
    run_id: str
    created_at: str
    display_label: str
    status: Literal["succeeded"]
    scenario_name: str
    input_source_type: str
    input_format: str
    solver_mode: str
    time_unit: str
    input_unit: str
    entered_time_limit: float
    driver_time_limit: float
    max_iterations: int | None
    runtime_seconds: float
    normalized_result: dict[str, JSONValue]
    analysis: dict[str, JSONValue]
    progress_events: list[ProgressEventRecord]
    manager_summary: ManagerSummary
    validation_warnings: list[str]
    solver_warnings: list[str]
    explanation: str
    metadata: dict[str, JSONValue]


class HistoryState(TypedDict):
    run_history: list[RunRecord]
    selected_run_id: str | None
    active_view: ActiveView


def _json_snapshot(value: Any, *, label: str) -> Any:
    """Return a detached JSON value, rejecting unsupported values and NaNs."""
    try:
        serialized = json.dumps(value, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must contain only JSON-compatible values.") from exc
    return json.loads(serialized)


def normalize_progress_event(progress: SolverProgress) -> ProgressEventRecord:
    """Convert one solver callback event into an independent JSON snapshot."""
    applied_path = (
        None
        if progress.applied_path is None
        else [int(node) for node in progress.applied_path]
    )
    event: ProgressEventRecord = {
        "iteration": int(progress.iteration),
        "current_driver_count": int(progress.current_driver_count),
        "current_total_time": float(progress.current_total_time),
        "current_max_driver_time": float(progress.current_max_driver_time),
        "applied_path": applied_path,
        "message": str(progress.message),
    }
    return cast(
        ProgressEventRecord,
        _json_snapshot(event, label="progress event"),
    )


def build_run_record(
    *,
    scenario_name: str,
    input_source_type: str,
    input_format: str,
    solver_mode: str,
    time_unit: str,
    input_unit: str,
    entered_time_limit: float,
    driver_time_limit: float,
    max_iterations: int | None,
    runtime_seconds: float,
    result: Mapping[str, Any],
    analysis: Mapping[str, Any],
    explanation: str,
    progress_events: Sequence[Mapping[str, Any]],
    run_id: str | None = None,
    created_at: str | None = None,
) -> RunRecord:
    """Build a successful, detached run record for UI history or JSON export."""
    normalized_result = cast(
        dict[str, JSONValue],
        _json_snapshot(result, label="solver result"),
    )
    normalized_analysis = cast(
        dict[str, JSONValue],
        _json_snapshot(analysis, label="analysis"),
    )
    normalized_events = cast(
        list[ProgressEventRecord],
        _json_snapshot(list(progress_events), label="progress events"),
    )

    initial_driver_count = int(normalized_result["initial_driver_count"])
    final_driver_count = int(normalized_result["final_driver_count"])
    initial_total_time = float(normalized_result["initial_total_time"])
    final_total_time = float(normalized_result["final_total_time"])
    manager_summary: ManagerSummary = {
        "initial_driver_count": initial_driver_count,
        "final_driver_count": final_driver_count,
        "drivers_saved": initial_driver_count - final_driver_count,
        "initial_total_time": initial_total_time,
        "final_total_time": final_total_time,
        "total_time_saved": initial_total_time - final_total_time,
        "max_driver_time": float(normalized_result["max_driver_time"]),
        "feasible": bool(normalized_result["feasible"]),
    }

    validation = normalized_result.get("validation", {})
    if not isinstance(validation, dict):
        raise TypeError("solver result validation must be a JSON object.")
    raw_validation_warnings = validation.get("warnings", [])
    if not isinstance(raw_validation_warnings, list) or not all(
        isinstance(warning, str) for warning in raw_validation_warnings
    ):
        raise TypeError("validation warnings must be a list of strings.")
    validation_warnings = list(raw_validation_warnings)

    solver_warnings: list[str] = []
    if solver_mode == "karp_mmc":
        solver_warnings.append(
            "Karp/MMC is experimental and may not handle every residual structure."
        )

    record_id = str(uuid.uuid4()) if run_id is None else str(run_id)
    timestamp = (
        datetime.now(timezone.utc).isoformat()
        if created_at is None
        else str(created_at)
    )
    solver_label = (
        "Karp/MMC" if solver_mode == "karp_mmc" else "Bellman-Ford discharge"
    )
    display_label = (
        f"{scenario_name} | {solver_label} | "
        f"{initial_driver_count} → {final_driver_count} drivers"
    )

    record: RunRecord = {
        "schema_version": 1,
        "run_id": record_id,
        "created_at": timestamp,
        "display_label": display_label,
        "status": "succeeded",
        "scenario_name": str(scenario_name),
        "input_source_type": str(input_source_type),
        "input_format": str(input_format),
        "solver_mode": str(solver_mode),
        "time_unit": str(time_unit),
        "input_unit": str(input_unit),
        "entered_time_limit": float(entered_time_limit),
        "driver_time_limit": float(driver_time_limit),
        "max_iterations": (
            None if max_iterations is None else int(max_iterations)
        ),
        "runtime_seconds": float(runtime_seconds),
        "normalized_result": normalized_result,
        "analysis": normalized_analysis,
        "progress_events": normalized_events,
        "manager_summary": manager_summary,
        "validation_warnings": validation_warnings,
        "solver_warnings": solver_warnings,
        "explanation": str(explanation),
        "metadata": {},
    }
    return cast(RunRecord, _json_snapshot(record, label="run record"))


def new_history_state() -> HistoryState:
    """Return a fresh, empty session-history state."""
    return {
        "run_history": [],
        "selected_run_id": None,
        "active_view": "summary",
    }


def _snapshot_state(state: Mapping[str, Any]) -> HistoryState:
    return cast(HistoryState, _json_snapshot(state, label="history state"))


def add_run_record(
    state: Mapping[str, Any],
    record: Mapping[str, Any],
    limit: int = 20,
) -> HistoryState:
    """Insert a successful run at the front without mutating either input."""
    if limit < 1:
        raise ValueError("History limit must be at least 1.")
    current = _snapshot_state(state)
    stored_record = cast(
        RunRecord,
        _json_snapshot(record, label="run record"),
    )
    history = [stored_record, *current["run_history"]][:limit]
    return {
        "run_history": history,
        "selected_run_id": stored_record["run_id"],
        "active_view": "summary",
    }


def select_run(state: Mapping[str, Any], run_id: str) -> HistoryState:
    """Select a stored run, falling back to the newest run when necessary."""
    current = _snapshot_state(state)
    history = current["run_history"]
    available_ids = {record["run_id"] for record in history}
    selected_run_id = (
        run_id
        if run_id in available_ids
        else history[0]["run_id"] if history else None
    )
    return {
        "run_history": history,
        "selected_run_id": selected_run_id,
        "active_view": "summary",
    }


def set_active_view(state: Mapping[str, Any], view: str) -> HistoryState:
    """Switch between the manager summary and engineering details views."""
    if view not in ("summary", "details"):
        raise ValueError("Active view must be 'summary' or 'details'.")
    current = _snapshot_state(state)
    return {
        "run_history": current["run_history"],
        "selected_run_id": current["selected_run_id"],
        "active_view": cast(ActiveView, view),
    }


def clear_history(state: Mapping[str, Any]) -> HistoryState:
    """Return fresh empty state without mutating the supplied state."""
    _snapshot_state(state)
    return new_history_state()


def get_selected_run(state: Mapping[str, Any]) -> RunRecord | None:
    """Return a detached selected run, or the newest run as a safe fallback."""
    current = _snapshot_state(state)
    history = current["run_history"]
    if not history:
        return None
    selected_run_id = current["selected_run_id"]
    selected = next(
        (
            record
            for record in history
            if record["run_id"] == selected_run_id
        ),
        history[0],
    )
    return cast(RunRecord, _json_snapshot(selected, label="selected run"))
