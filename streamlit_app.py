"""Interactive constrained-routing workbench for RouteOpt Agent.

The manager-facing summary remains the default result view. Successful runs are
stored as bounded, JSON-compatible snapshots so the same browser session can
reopen prior summaries and inspect already-available engineering diagnostics.
"""

from __future__ import annotations

from pathlib import Path
import time
from typing import Any

import matplotlib.pyplot as plt

from src.agent_workflow import run_routing_workflow
from src.run_history import (
    HistoryState,
    RunRecord,
    add_run_record,
    build_run_record,
    clear_history,
    get_selected_run,
    new_history_state,
    normalize_progress_event,
    select_run,
    set_active_view,
)
from src.ui_utils import (
    caption_for_data_unit,
    convert_time_limit_to_data_units,
    format_route_time_for_display,
    format_runtime_seconds,
)


_HISTORY_KEYS = ("run_history", "selected_run_id", "active_view")
_HISTORY_SELECTOR_KEY = "history_selector_id"


def _list_sample_files() -> list[Path]:
    """Return the bundled ``data/*.txt`` scenario paths."""
    data_dir = Path(__file__).parent / "data"
    return sorted(data_dir.glob("*.txt"))


def _read_session_history(st: Any) -> HistoryState:
    """Initialize and read the canonical history keys from Streamlit state."""
    defaults = new_history_state()
    for key in _HISTORY_KEYS:
        if key not in st.session_state:
            st.session_state[key] = defaults[key]
    return {
        "run_history": st.session_state["run_history"],
        "selected_run_id": st.session_state["selected_run_id"],
        "active_view": st.session_state["active_view"],
    }


def _write_session_history(st: Any, state: HistoryState) -> None:
    """Write a state returned by ``src.run_history`` to Streamlit state."""
    for key in _HISTORY_KEYS:
        st.session_state[key] = state[key]


def _select_session_run(st: Any, run_id: str | None = None) -> None:
    """Select a session run through the pure history transition."""
    selected_id = run_id or st.session_state.get(_HISTORY_SELECTOR_KEY)
    if not isinstance(selected_id, str):
        return
    state = select_run(_read_session_history(st), selected_id)
    _write_session_history(st, state)


def _clear_session_history(st: Any) -> None:
    """Clear canonical history and its independent selector widget state."""
    state = clear_history(_read_session_history(st))
    _write_session_history(st, state)
    st.session_state.pop(_HISTORY_SELECTOR_KEY, None)


def _switch_session_view(st: Any, view: str) -> None:
    """Switch the selected run between summary and details views."""
    state = set_active_view(_read_session_history(st), view)
    _write_session_history(st, state)


def _render_session_history_controls(st: Any) -> None:
    """Render newest-first session run selection and clearing controls."""
    state = _read_session_history(st)
    history = state["run_history"]

    with st.sidebar:
        st.header("Session Runs")
        if not history:
            st.caption("Successful runs from this browser session will appear here.")
            return

        run_ids = [record["run_id"] for record in history]
        labels = {
            record["run_id"]: record["display_label"] for record in history
        }
        selected_id = state["selected_run_id"]
        if selected_id not in run_ids:
            selected_id = run_ids[0]
            _select_session_run(st, selected_id)

        widget_value = st.session_state.get(_HISTORY_SELECTOR_KEY)
        if widget_value not in run_ids:
            st.session_state[_HISTORY_SELECTOR_KEY] = selected_id

        st.selectbox(
            "Select a completed run",
            run_ids,
            format_func=lambda run_id: labels[run_id],
            key=_HISTORY_SELECTOR_KEY,
            on_change=_select_session_run,
            args=(st,),
        )
        st.button(
            "Clear Session History",
            on_click=_clear_session_history,
            args=(st,),
        )


def _render_route_table(
    st: Any,
    pd: Any,
    routes: Any,
    *,
    empty_message: str,
) -> None:
    """Render a driver-to-stops mapping with the existing table layout."""
    if not isinstance(routes, dict) or not routes:
        st.info(empty_message)
        return
    dataframe = pd.DataFrame.from_dict(routes, orient="index")
    dataframe.index.name = "Driver"
    dataframe.columns = [
        f"Stop {index + 1}" for index in range(dataframe.shape[1])
    ]
    st.dataframe(dataframe)


def _solver_display_name(solver_mode: str) -> str:
    if solver_mode == "karp_mmc":
        return "Experimental Karp/MMC"
    return "Bellman-Ford discharge"


def _render_manager_summary(st: Any, pd: Any, record: RunRecord) -> None:
    """Render the selected run's manager-facing outcome summary."""
    result = record["normalized_result"]
    summary = record["manager_summary"]
    data_unit = record["time_unit"]

    st.subheader("Run Summary")
    st.caption(
        f"{record['scenario_name']} | "
        f"{_solver_display_name(record['solver_mode'])} | "
        f"{record['created_at']}"
    )
    st.button(
        "View Run Details",
        key=f"details-{record['run_id']}",
        on_click=_switch_session_view,
        args=(st, "details"),
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Initial drivers", summary["initial_driver_count"])
    col2.metric("Final drivers", summary["final_driver_count"])
    col3.metric("Drivers saved", summary["drivers_saved"])

    col4, col5, col6 = st.columns(3)
    col4.metric(
        "Initial total time",
        format_route_time_for_display(summary["initial_total_time"], data_unit),
    )
    col5.metric(
        "Final total time",
        format_route_time_for_display(summary["final_total_time"], data_unit),
    )
    col6.metric(
        "Time saved",
        format_route_time_for_display(summary["total_time_saved"], data_unit),
    )

    col7, col8, col9 = st.columns(3)
    col7.metric(
        "Max driver time",
        format_route_time_for_display(summary["max_driver_time"], data_unit),
    )
    col8.metric("Feasibility", "Feasible" if summary["feasible"] else "Not feasible")
    col9.metric(
        "Workflow runtime",
        format_runtime_seconds(record["runtime_seconds"]),
    )

    st.subheader("Explanation")
    st.write(record["explanation"])

    st.subheader("Agent Trace")
    trace_items = [
        "Scenario parsed",
        "Constraint interpreted",
        "Solver selected",
        "Optimization tool executed",
        "Feasibility evaluated",
        "Recommendation generated",
    ]
    st.markdown("\n".join(f"- {item}" for item in trace_items))

    st.subheader("Final routes (driver → stops)")
    routes = result.get("routes", {})
    _render_route_table(
        st,
        pd,
        routes,
        empty_message="No route information returned.",
    )

    if summary["feasible"] and isinstance(routes, dict) and routes:
        st.subheader("Route length overview")
        lengths = {driver: len(stops) for driver, stops in routes.items()}
        figure, axis = plt.subplots()
        axis.bar(lengths.keys(), lengths.values())
        axis.set_xlabel("Driver")
        axis.set_ylabel("Number of stops")
        axis.set_title("Stops per driver")
        st.pyplot(figure)
        plt.close(figure)


def _render_run_details(st: Any, pd: Any, record: RunRecord) -> None:
    """Render diagnostics already captured in the selected run record."""
    st.button(
        "Back to Summary",
        key=f"summary-{record['run_id']}",
        on_click=_switch_session_view,
        args=(st, "summary"),
    )

    st.header("Run Details")
    st.metric(
        "Workflow runtime",
        format_runtime_seconds(record["runtime_seconds"]),
    )
    result = record["normalized_result"]

    st.subheader("Run configuration")
    st.json(
        {
            "scenario_name": record["scenario_name"],
            "input_source": record["input_source_type"],
            "input_format": record["input_format"],
            "solver_mode": record["solver_mode"],
            "time_unit": record["time_unit"],
            "input_unit": record["input_unit"],
            "entered_time_limit": record["entered_time_limit"],
            "normalized_driver_time_limit": record["driver_time_limit"],
            "max_iterations": record["max_iterations"],
            "runtime_seconds": record["runtime_seconds"],
            "run_id": record["run_id"],
            "created_at": record["created_at"],
        }
    )

    st.subheader("Execution diagnostics")
    st.json(
        {
            "iterations": result.get("iterations"),
            "terminated_by_iteration_limit": bool(
                result.get("terminated_by_iteration_limit", False)
            ),
            "feasible": bool(result.get("feasible", False)),
        }
    )
    st.markdown("**Validation report**")
    st.json(result.get("validation", {}))

    st.markdown("**Validation warnings**")
    if record["validation_warnings"]:
        for warning in record["validation_warnings"]:
            st.warning(warning)
    else:
        st.caption("No validation warnings were reported.")

    st.markdown("**Solver warnings**")
    if record["solver_warnings"]:
        for warning in record["solver_warnings"]:
            st.warning(warning)
    else:
        st.caption("No solver-maturity warnings were reported.")

    negative_cycle = result.get("negative_cycle")
    if negative_cycle is not None:
        st.markdown("**Raw negative_cycle field**")
        st.json(negative_cycle)

    st.subheader("Augmentation progress")
    progress_events = record["progress_events"]
    if progress_events:
        progress_frame = pd.DataFrame(
            progress_events,
            columns=[
                "iteration",
                "current_driver_count",
                "current_total_time",
                "current_max_driver_time",
                "applied_path",
                "message",
            ],
        )
        st.dataframe(progress_frame)
    else:
        st.info("No successful augmentation events were emitted for this run.")

    st.markdown("**Final result applied_paths (execution order)**")
    st.json(result.get("applied_paths", []))
    st.caption(
        "Structural augmentation classification and per-step route snapshots "
        "require later solver instrumentation; they are not inferred here."
    )

    st.subheader("Route comparison")
    initial_column, final_column = st.columns(2)
    with initial_column:
        st.markdown("**Initial routes**")
        _render_route_table(
            st,
            pd,
            result.get("initial_routes", {}),
            empty_message="No initial routes were returned.",
        )
    with final_column:
        st.markdown("**Final routes**")
        _render_route_table(
            st,
            pd,
            result.get("routes", {}),
            empty_message="No final routes were returned.",
        )
    st.caption("Per-step route states are not available in the current solver contract.")

    st.subheader("Raw normalized result")
    st.json(result)


def _run_streamlit_app() -> None:
    """Execute the Streamlit UI with session-scoped successful-run history."""
    import pandas as pd
    import streamlit as st

    from src.custom_input import (
        normalize_load_rows_to_scenario_text,
        parse_csv_loads,
        parse_txt_loads,
        write_temp_scenario_file,
    )

    st.set_page_config(
        page_title="RouteOpt Agent",
        page_icon="🚚",
        layout="wide",
    )
    _read_session_history(st)

    st.title("🚚 RouteOpt Agent")
    st.caption(
        "Explore constrained-routing scenarios, compare residual-graph solvers, "
        "and inspect feasibility and route-time results."
    )

    scenario_path: Path | None = None
    scenario_text: str | None = None
    scenario_name = ""
    input_source_type = ""
    input_format = ""

    with st.sidebar:
        st.header("Scenario & Parameters")
        mode = st.radio(
            "Input mode",
            ("Bundled sample", "Upload file", "Manual entry"),
        )
        solver_choice = st.radio(
            "Solver mode",
            ("Bellman discharge", "Experimental Karp/MMC"),
            index=0,
            help=(
                "Bellman discharge is the stable default. Karp/MMC is "
                "experimental and may fail on some scenarios."
            ),
        )
        solver_mode = (
            "bellman_discharge"
            if solver_choice == "Bellman discharge"
            else "karp_mmc"
        )
        st.caption(
            "Bellman discharge is the stable default. Karp/MMC is "
            "experimental and may fail on some scenarios."
        )
        data_unit = st.selectbox(
            "Data route-time unit",
            ("Minutes", "Hours", "Abstract units"),
            index=1,
        )
        st.caption(caption_for_data_unit(data_unit))
        input_unit = st.selectbox(
            "Enter driver time limit as",
            ("Same as data unit", "Hours", "Minutes"),
            index=0,
        )
        time_limit_input = st.number_input(
            "Driver time limit",
            min_value=0.0,
            value=12.0,
            step=0.5,
        )
        time_limit_backend = convert_time_limit_to_data_units(
            time_limit_input,
            input_unit,
            data_unit,
        )

        if mode == "Bundled sample":
            sample_files = _list_sample_files()
            file_options = {path.name: path for path in sample_files}
            selected_name = st.selectbox(
                "Select bundled scenario",
                list(file_options.keys()),
            )
            if selected_name is not None:
                scenario_path = file_options[selected_name]
                scenario_name = selected_name
                input_source_type = "bundled"
                input_format = "txt"
        elif mode == "Upload file":
            uploaded = st.file_uploader(
                "Upload a scenario file (.txt or .csv)",
                type=["txt", "csv"],
            )
            if uploaded is not None:
                scenario_name = uploaded.name
                input_source_type = "upload"
                if getattr(uploaded, "size", 0) > 500_000:
                    st.error("File too large (max 500 KB).")
                else:
                    suffix = Path(uploaded.name).suffix.lower()
                    input_format = suffix.removeprefix(".")
                    try:
                        content = uploaded.getvalue().decode(
                            "utf-8",
                            errors="replace",
                        )
                        if suffix == ".txt":
                            rows = parse_txt_loads(content)
                        elif suffix == ".csv":
                            rows = parse_csv_loads(content)
                        else:
                            st.error("Unsupported file extension. Use .txt or .csv.")
                            rows = None
                    except ValueError as exc:
                        st.error(str(exc))
                        rows = None
                    if rows:
                        scenario_text = normalize_load_rows_to_scenario_text(rows)
        else:
            scenario_name = "Manual entry"
            input_source_type = "manual"
            raw_text = st.text_area(
                "Paste or type load rows (TXT or CSV format)",
                height=200,
            )
            if raw_text:
                nonblank_lines = [
                    line for line in raw_text.splitlines() if line.strip()
                ]
                if nonblank_lines:
                    first = nonblank_lines[0].strip()
                    header_parts = [
                        heading.strip().lower() for heading in first.split(",")
                    ]
                    is_csv_header = header_parts == [
                        "pickup_x",
                        "pickup_y",
                        "dropoff_x",
                        "dropoff_y",
                    ]
                    input_format = "csv" if is_csv_header else "txt"
                    try:
                        if is_csv_header:
                            rows = parse_csv_loads("\n".join(nonblank_lines))
                        else:
                            rows = parse_txt_loads("\n".join(nonblank_lines))
                    except ValueError as exc:
                        st.error(str(exc))
                        rows = None
                    if rows:
                        scenario_text = normalize_load_rows_to_scenario_text(rows)

        run_button = st.button("Run Optimization")

    if run_button:
        progress_events: list[dict[str, Any]] = []
        temp_file: Path | None = None
        status_placeholder = None
        if scenario_path is None and scenario_text is None:
            st.error("No valid scenario selected or uploaded.")
        else:
            try:
                execution_path = scenario_path
                if execution_path is None:
                    temp_file = write_temp_scenario_file(scenario_text or "")
                    execution_path = temp_file

                status_placeholder = st.empty()
                start_time = time.perf_counter()

                def progress_cb(progress: Any) -> None:
                    progress_events.append(normalize_progress_event(progress))
                    elapsed = time.perf_counter() - start_time
                    status = (
                        f"Drivers: {progress.current_driver_count} | "
                        f"Total: {format_route_time_for_display(progress.current_total_time, data_unit)} | "
                        f"Max: {format_route_time_for_display(progress.current_max_driver_time, data_unit)} | "
                        f"Elapsed: {elapsed:.2f}s"
                    )
                    status_placeholder.info(status)

                workflow_state = run_routing_workflow(
                    str(execution_path),
                    time_limit=time_limit_backend,
                    solver_mode=solver_mode,
                    progress_callback=progress_cb,
                )
                runtime_seconds = time.perf_counter() - start_time

                if workflow_state.errors:
                    st.error("\n".join(workflow_state.errors))
                elif (
                    workflow_state.result is None
                    or workflow_state.analysis is None
                    or workflow_state.explanation is None
                ):
                    st.error("The workflow completed without a full result record.")
                else:
                    record = build_run_record(
                        scenario_name=scenario_name,
                        input_source_type=input_source_type,
                        input_format=input_format,
                        solver_mode=solver_mode,
                        time_unit=data_unit,
                        input_unit=input_unit,
                        entered_time_limit=float(time_limit_input),
                        driver_time_limit=float(time_limit_backend),
                        max_iterations=None,
                        runtime_seconds=runtime_seconds,
                        result=workflow_state.result,
                        analysis=workflow_state.analysis,
                        explanation=workflow_state.explanation,
                        progress_events=progress_events,
                    )
                    history_state = add_run_record(
                        _read_session_history(st),
                        record,
                    )
                    _write_session_history(st, history_state)
                    st.session_state[_HISTORY_SELECTOR_KEY] = record["run_id"]
            except Exception as exc:
                st.error(str(exc))
            finally:
                if status_placeholder is not None:
                    status_placeholder.empty()
                if temp_file is not None and temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass

    _render_session_history_controls(st)
    history_state = _read_session_history(st)
    selected_record = get_selected_run(history_state)
    if selected_record is not None:
        if history_state["active_view"] == "details":
            _render_run_details(st, pd, selected_record)
        else:
            _render_manager_summary(st, pd, selected_record)


if __name__ == "__main__":
    _run_streamlit_app()
