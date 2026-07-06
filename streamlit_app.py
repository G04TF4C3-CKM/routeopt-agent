# Streamlit demo for RouteOpt Agent
"""A minimal Streamlit front‑end that wraps the existing RouteOpt Agent workflow.

The UI lets the user:
1. Pick one of the bundled scenario files under `data/`.
2. Set a driver‑time limit (default 12.0).
3. Run the workflow and view the key result metrics.
4. See a short textual explanation and a table of final routes.
5. (If feasible) visualise route lengths with a simple Matplotlib bar chart.

The implementation stays lightweight – no custom CSS, no heavy dependencies –
and calls the unchanged backend (`src.agent_workflow.run_routing_workflow`).
"""

from pathlib import Path
import matplotlib.pyplot as plt

from src.agent_workflow import run_routing_workflow

# ---------------------------------------------------------------------------
# Helper to discover bundled scenario files
# ---------------------------------------------------------------------------

def _list_sample_files() -> list[Path]:
    """Return a list of ``Path`` objects for ``data/*.txt`` files.

    The function is isolated for easy testing and for potential future reuse.
    """
    data_dir = Path(__file__).parent / "data"
    return sorted(data_dir.glob("*.txt"))

# ---------------------------------------------------------------------------
def _run_streamlit_app():
    """Execute the Streamlit UI with three input modes.

    The UI is imported lazily to keep the module import‑able in test environments.
    All validation is performed locally using :pymod:`src.custom_input`.
    """
    import streamlit as st
    import pandas as pd
    from pathlib import Path
    from src.custom_input import (
        parse_txt_loads,
        parse_csv_loads,
        normalize_load_rows_to_scenario_text,
        write_temp_scenario_file,
    )

    st.title("🚚 RouteOpt Agent – Interactive Demo")
    st.caption("Run the optimizer on bundled, uploaded, or manually entered scenarios.")

    # Sidebar – mode selector and common parameters
    with st.sidebar:
        st.header("Scenario & Parameters")
        mode = st.radio(
            "Input mode",
            ("Bundled sample", "Upload file", "Manual entry"),
        )
        time_limit = st.slider(
            "Driver time limit (hours)", min_value=1.0, max_value=24.0, value=12.0, step=0.5
        )

        scenario_path: Path | None = None
        temp_file: Path | None = None

        if mode == "Bundled sample":
            sample_files = _list_sample_files()
            file_options = {p.name: p for p in sample_files}
            selected_name = st.selectbox("Select bundled scenario", list(file_options.keys()))
            scenario_path = file_options[selected_name]
        elif mode == "Upload file":
            uploaded = st.file_uploader(
                "Upload a scenario file (.txt or .csv)", type=["txt", "csv"]
            )
            if uploaded is not None:
                if getattr(uploaded, "size", 0) > 500_000:
                    st.error("File too large (max 500 KB).")
                else:
                    suffix = Path(uploaded.name).suffix.lower()
                    try:
                        content = uploaded.read().decode("utf-8", errors="replace")
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
                        temp_file = write_temp_scenario_file(scenario_text)
                        scenario_path = temp_file
        else:  # Manual entry
            raw_text = st.text_area(
                "Paste or type load rows (TXT or CSV format)", height=200
            )
            if raw_text:
                nonblank_lines = [ln for ln in raw_text.splitlines() if ln.strip()]
                if nonblank_lines:
                    first = nonblank_lines[0].strip()
                    header_parts = [h.strip().lower() for h in first.split(",")]
                    is_csv_header = header_parts == ["pickup_x", "pickup_y", "dropoff_x", "dropoff_y"]
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
                        temp_file = write_temp_scenario_file(scenario_text)
                        scenario_path = temp_file
        run_button = st.button("Run Optimization")

    if run_button:
        if scenario_path is None:
            st.error("No valid scenario selected or uploaded.")
        else:
            try:
                with st.spinner("Running optimizer…"):
                    state = run_routing_workflow(str(scenario_path), time_limit=time_limit)
                if state.errors:
                    st.error("\n".join(state.errors))
                else:
                    result = state.result
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Initial drivers", result.get("initial_driver_count", "-"))
                    col2.metric("Final drivers", result.get("final_driver_count", "-"))
                    saved = result.get("initial_driver_count", 0) - result.get("final_driver_count", 0)
                    col3.metric("Drivers saved", saved)
                    col4, col5, col6 = st.columns(3)
                    col4.metric("Initial total time", f"{result.get('initial_total_time', 0):.3f}")
                    col5.metric("Final total time", f"{result.get('final_total_time', 0):.3f}")
                    time_saved = result.get("initial_total_time", 0) - result.get("final_total_time", 0)
                    col6.metric("Time saved", f"{time_saved:.3f}")
                    col7, col8 = st.columns(2)
                    col7.metric("Max driver time", f"{result.get('max_driver_time', 0):.3f}")
                    feasibility = "Feasible" if result.get("feasible") else "Not feasible"
                    col8.metric("Feasibility", feasibility)
                    st.subheader("Explanation")
                    st.write(state.explanation)
                    st.subheader("Final routes (driver → stops)")
                    routes = result.get("routes", {})
                    if routes:
                        df = pd.DataFrame.from_dict(routes, orient="index")
                        df.index.name = "Driver"
                        df.columns = [f"Stop {i+1}" for i in range(df.shape[1])]
                        st.dataframe(df)
                    else:
                        st.info("No route information returned.")
                    if result.get("feasible") and routes:
                        st.subheader("Route length overview")
                        lengths = {d: len(s) for d, s in routes.items()}
                        fig, ax = plt.subplots()
                        ax.bar(lengths.keys(), lengths.values())
                        ax.set_xlabel("Driver")
                        ax.set_ylabel("Number of stops")
                        ax.set_title("Stops per driver")
                        st.pyplot(fig)
            finally:
                if temp_file is not None and temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass

# Entry point for ``streamlit run``
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _run_streamlit_app()
