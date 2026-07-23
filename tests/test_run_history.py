from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
import importlib
import importlib.util
import json
from types import ModuleType
from typing import Any

import pytest

from src.solver_types import SolverProgress


RUN_HISTORY_SPEC = importlib.util.find_spec("src.run_history")
requires_run_history = pytest.mark.skipif(
    RUN_HISTORY_SPEC is None,
    reason="src.run_history has not been implemented yet",
)


def _sample_result() -> dict[str, Any]:
    return {
        "scenario_path": "data/sample_8_loads.txt",
        "load_count": 4,
        "time_limit": 12.0,
        "iterations": 1,
        "terminated_by_iteration_limit": False,
        "negative_cycle": None,
        "initial_driver_count": 2,
        "final_driver_count": 1,
        "initial_total_time": 20.0,
        "final_total_time": 11.5,
        "max_driver_time": 11.5,
        "feasible": True,
        "initial_routes": {"1": [1, 2], "2": [3, 4]},
        "routes": {"1": [1, 2, 3, 4]},
        "applied_paths": [[-1, 2, 1, 0]],
        "validation": {
            "valid": True,
            "load_count": 4,
            "warnings": ["Fixture validation warning."],
        },
    }


def _sample_analysis() -> dict[str, Any]:
    return {
        "drivers_saved": 1,
        "driver_reduction_pct": 50.0,
        "total_time_saved": 8.5,
        "total_time_reduction_pct": 42.5,
        "is_feasible": True,
    }


def _sample_progress_events() -> list[dict[str, Any]]:
    return [
        {
            "iteration": 1,
            "current_driver_count": 1,
            "current_total_time": 11.5,
            "current_max_driver_time": 11.5,
            "applied_path": [-1, 2, 1, 0],
            "message": "discharge applied",
        }
    ]


def _run_record_kwargs(**overrides: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "scenario_name": "Sample eight-load scenario",
        "input_source_type": "bundled",
        "input_format": "txt",
        "solver_mode": "bellman_discharge",
        "time_unit": "hours",
        "input_unit": "hours",
        "entered_time_limit": 12.0,
        "driver_time_limit": 12.0,
        "max_iterations": 50,
        "runtime_seconds": 0.25,
        "result": _sample_result(),
        "analysis": _sample_analysis(),
        "explanation": "Reduced the plan by one driver while preserving feasibility.",
        "progress_events": _sample_progress_events(),
    }
    kwargs.update(overrides)
    return kwargs


@pytest.fixture
def run_history() -> ModuleType:
    if RUN_HISTORY_SPEC is None:
        pytest.skip("src.run_history has not been implemented yet")
    return importlib.import_module("src.run_history")


def test_run_history_module_exists():
    assert RUN_HISTORY_SPEC is not None, (
        "src.run_history is missing; implement the Green Team run-history module."
    )


@requires_run_history
def test_normalize_progress_event_returns_independent_json_snapshot(run_history):
    applied_path = [-1, 2, 1, 0]
    progress = SolverProgress(
        iteration=3,
        current_driver_count=2,
        current_total_time=18.25,
        current_max_driver_time=10.5,
        applied_path=applied_path,
        message="discharge applied",
    )

    normalized = run_history.normalize_progress_event(progress)

    assert normalized == {
        "iteration": 3,
        "current_driver_count": 2,
        "current_total_time": 18.25,
        "current_max_driver_time": 10.5,
        "applied_path": [-1, 2, 1, 0],
        "message": "discharge applied",
    }
    json.dumps(normalized, allow_nan=False)

    applied_path.append(99)
    progress.applied_path.append(100)
    progress.message = "mutated"

    assert normalized["applied_path"] == [-1, 2, 1, 0]
    assert normalized["message"] == "discharge applied"


@requires_run_history
def test_build_run_record_contains_required_fields_and_manager_summary(run_history):
    record = run_history.build_run_record(
        **_run_record_kwargs(
            run_id="run-fixed",
            created_at="2026-07-23T12:34:56+00:00",
        )
    )

    assert record["schema_version"] == 1
    assert record["run_id"] == "run-fixed"
    assert record["created_at"] == "2026-07-23T12:34:56+00:00"
    assert isinstance(record["display_label"], str)
    assert record["display_label"]
    assert record["status"] == "succeeded"
    assert record["scenario_name"] == "Sample eight-load scenario"
    assert record["input_source_type"] == "bundled"
    assert record["input_format"] == "txt"
    assert record["solver_mode"] == "bellman_discharge"
    assert record["time_unit"] == "hours"
    assert record["input_unit"] == "hours"
    assert record["entered_time_limit"] == 12.0
    assert record["driver_time_limit"] == 12.0
    assert record["max_iterations"] == 50
    assert record["runtime_seconds"] == 0.25
    assert record["normalized_result"] == _sample_result()
    assert record["progress_events"] == _sample_progress_events()
    assert record["manager_summary"] == {
        "initial_driver_count": 2,
        "final_driver_count": 1,
        "drivers_saved": 1,
        "initial_total_time": 20.0,
        "final_total_time": 11.5,
        "total_time_saved": 8.5,
        "max_driver_time": 11.5,
        "feasible": True,
    }
    assert record["validation_warnings"] == ["Fixture validation warning."]
    assert record["solver_warnings"] == []
    assert record["explanation"].startswith("Reduced the plan")
    assert record["metadata"] == {}


@requires_run_history
def test_build_run_record_is_strictly_json_serializable(run_history):
    record = run_history.build_run_record(**_run_record_kwargs())

    json.dumps(record, allow_nan=False)


@requires_run_history
def test_build_run_record_adds_warning_only_for_experimental_solver(run_history):
    experimental = run_history.build_run_record(
        **_run_record_kwargs(solver_mode="karp_mmc")
    )
    stable = run_history.build_run_record(
        **_run_record_kwargs(solver_mode="bellman_discharge")
    )

    assert any(
        "experimental" in warning.casefold()
        for warning in experimental["solver_warnings"]
    )
    assert not any(
        "experimental" in warning.casefold()
        for warning in stable["solver_warnings"]
    )


@requires_run_history
def test_build_run_record_snapshots_all_caller_owned_inputs(run_history):
    result = _sample_result()
    analysis = _sample_analysis()
    progress_events = _sample_progress_events()
    record = run_history.build_run_record(
        **_run_record_kwargs(
            result=result,
            analysis=analysis,
            progress_events=progress_events,
        )
    )
    original_record = deepcopy(record)

    result["routes"]["1"].append(99)
    result["applied_paths"][0].append(99)
    result["validation"]["warnings"].append("Later warning.")
    analysis["drivers_saved"] = 99
    progress_events[0]["applied_path"].append(99)
    progress_events[0]["message"] = "mutated"

    assert record == original_record


@requires_run_history
def test_build_run_record_generates_unique_ids_and_utc_timestamps(run_history):
    first = run_history.build_run_record(**_run_record_kwargs())
    second = run_history.build_run_record(**_run_record_kwargs())

    assert first["run_id"] != second["run_id"]
    for record in (first, second):
        parsed = datetime.fromisoformat(record["created_at"].replace("Z", "+00:00"))
        assert parsed.utcoffset() == timedelta(0)


@requires_run_history
def test_build_run_record_preserves_injected_id_and_timestamp(run_history):
    record = run_history.build_run_record(
        **_run_record_kwargs(
            run_id="deterministic-run-id",
            created_at="2025-01-02T03:04:05Z",
        )
    )

    assert record["run_id"] == "deterministic-run-id"
    assert record["created_at"] == "2025-01-02T03:04:05Z"


@requires_run_history
def test_build_run_record_rejects_non_json_values(run_history):
    result = _sample_result()
    result["unsupported"] = object()

    with pytest.raises((TypeError, ValueError)):
        run_history.build_run_record(**_run_record_kwargs(result=result))


@requires_run_history
def test_new_history_state_has_expected_shape(run_history):
    assert run_history.new_history_state() == {
        "run_history": [],
        "selected_run_id": None,
        "active_view": "summary",
    }


@requires_run_history
def test_add_run_record_is_immutable_and_snapshots_the_record(run_history):
    state = {
        "run_history": [],
        "selected_run_id": None,
        "active_view": "details",
    }
    original_state = deepcopy(state)
    record = run_history.build_run_record(
        **_run_record_kwargs(run_id="new-run")
    )
    original_record = deepcopy(record)

    updated = run_history.add_run_record(state, record)

    assert updated is not state
    assert state == original_state
    assert updated["run_history"] == [original_record]
    assert updated["selected_run_id"] == "new-run"
    assert updated["active_view"] == "summary"

    record["normalized_result"]["routes"]["1"].append(99)
    record["progress_events"][0]["applied_path"].append(99)
    assert updated["run_history"] == [original_record]


@requires_run_history
def test_add_run_record_uses_default_history_limit(run_history):
    state = run_history.new_history_state()

    for index in range(22):
        record = run_history.build_run_record(
            **_run_record_kwargs(
                run_id=f"run-{index}",
                created_at=f"2026-07-23T12:00:{index:02d}+00:00",
            )
        )
        state = run_history.add_run_record(state, record)

    assert len(state["run_history"]) == 20
    assert [record["run_id"] for record in state["run_history"]] == [
        f"run-{index}" for index in range(21, 1, -1)
    ]
    assert state["selected_run_id"] == "run-21"


@requires_run_history
def test_add_run_record_accepts_smaller_explicit_limit(run_history):
    state = run_history.new_history_state()

    for index in range(3):
        record = run_history.build_run_record(
            **_run_record_kwargs(run_id=f"run-{index}")
        )
        state = run_history.add_run_record(state, record, limit=2)

    assert [record["run_id"] for record in state["run_history"]] == [
        "run-2",
        "run-1",
    ]


def _state_with_two_runs(run_history):
    state = run_history.new_history_state()
    for run_id in ("older", "newer"):
        record = run_history.build_run_record(
            **_run_record_kwargs(run_id=run_id)
        )
        state = run_history.add_run_record(state, record)
    return state


@requires_run_history
def test_select_run_is_immutable_and_preserves_history_order(run_history):
    state = _state_with_two_runs(run_history)
    state = run_history.set_active_view(state, "details")
    original_state = deepcopy(state)

    updated = run_history.select_run(state, "older")

    assert updated is not state
    assert state == original_state
    assert updated["selected_run_id"] == "older"
    assert updated["active_view"] == "summary"
    assert updated["run_history"] == original_state["run_history"]


@requires_run_history
def test_select_run_falls_back_to_newest_and_handles_empty_history(run_history):
    state = _state_with_two_runs(run_history)

    fallback = run_history.select_run(state, "missing")
    empty = run_history.select_run(run_history.new_history_state(), "missing")

    assert fallback["selected_run_id"] == "newer"
    assert fallback["active_view"] == "summary"
    assert empty == run_history.new_history_state()


@requires_run_history
@pytest.mark.parametrize("view", ["summary", "details"])
def test_set_active_view_is_immutable_and_preserves_run_state(run_history, view):
    state = _state_with_two_runs(run_history)
    original_state = deepcopy(state)

    updated = run_history.set_active_view(state, view)

    assert updated is not state
    assert state == original_state
    assert updated["active_view"] == view
    assert updated["run_history"] == original_state["run_history"]
    assert updated["selected_run_id"] == original_state["selected_run_id"]


@requires_run_history
def test_set_active_view_rejects_unknown_view(run_history):
    with pytest.raises(ValueError, match="summary|details"):
        run_history.set_active_view(run_history.new_history_state(), "raw")


@requires_run_history
def test_clear_history_returns_fresh_empty_state_without_mutation(run_history):
    state = _state_with_two_runs(run_history)
    original_state = deepcopy(state)

    cleared = run_history.clear_history(state)

    assert state == original_state
    assert cleared == run_history.new_history_state()
    assert cleared is not state


@requires_run_history
def test_get_selected_run_returns_selection_or_safe_fallback(run_history):
    state = _state_with_two_runs(run_history)

    selected = run_history.get_selected_run(
        run_history.select_run(state, "older")
    )
    fallback_state = deepcopy(state)
    fallback_state["selected_run_id"] = "missing"
    fallback = run_history.get_selected_run(fallback_state)

    assert selected["run_id"] == "older"
    assert fallback["run_id"] == "newer"
    assert run_history.get_selected_run(run_history.new_history_state()) is None
