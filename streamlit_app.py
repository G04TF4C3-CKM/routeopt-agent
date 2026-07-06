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
# Streamlit UI – encapsulated in a function to avoid import at module load time
# ---------------------------------------------------------------------------

def _run_streamlit_app():
    """Execute the Streamlit UI.

    Importing ``streamlit`` and ``pandas`` inside the function prevents
    ``ModuleNotFoundError`` when the module is imported in a test environment
    that does not have the optional dependencies installed.
    """
    import streamlit as st
    import pandas as pd

    st.title("🚚 RouteOpt Agent – Interactive Demo")
    st.caption("Select a bundled scenario and run the optimization workflow.")

    # Sidebar controls
    with st.sidebar:
        st.header("Scenario & Parameters")
        sample_files = _list_sample_files()
        file_options = {p.name: p for p in sample_files}
        selected_name = st.selectbox("Select scenario file", options=list(file_options.keys()))
        selected_path = file_options[selected_name]
        time_limit = st.slider("Driver time limit (hours)", min_value=1.0, max_value=24.0, value=12.0, step=0.5)
        run_button = st.button("Run Optimization")

    if run_button:
        with st.spinner("Running optimizer…"):
            state = run_routing_workflow(str(selected_path), time_limit=time_limit)
        if state.errors:
            st.error("\n".join(state.errors))
            return
        result = state.result

        # Core metrics – displayed as Streamlit ``metric`` tiles for quick glance
        col1, col2, col3 = st.columns(3)
        col1.metric("Initial drivers", result.get("initial_driver_count", "-"))
        col2.metric("Final drivers", result.get("final_driver_count", "-"))
        driver_saved = result.get("initial_driver_count", 0) - result.get("final_driver_count", 0)
        col3.metric("Drivers saved", driver_saved)

        col4, col5, col6 = st.columns(3)
        col4.metric("Initial total time", f"{result.get('initial_total_time', 0):.3f}")
        col5.metric("Final total time", f"{result.get('final_total_time', 0):.3f}")
        time_saved = result.get("initial_total_time", 0) - result.get("final_total_time", 0)
        col6.metric("Time saved", f"{time_saved:.3f}")

        col7, col8 = st.columns(2)
        col7.metric("Max driver time", f"{result.get('max_driver_time', 0):.3f}")
        feasibility = "Feasible" if result.get("feasible") else "Not feasible"
        col8.metric("Feasibility", feasibility)

        # Explanation text
        st.subheader("Explanation")
        st.write(state.explanation)

        # Final routes table
        st.subheader("Final routes (driver → stops)")
        routes_dict = result.get("routes", {})
        if routes_dict:
            df_routes = pd.DataFrame.from_dict(routes_dict, orient="index")
            df_routes.index.name = "Driver"
            df_routes.columns = [f"Stop {i+1}" for i in range(df_routes.shape[1])]
            st.dataframe(df_routes)
        else:
            st.info("No route information returned.")

        # Simple visualization – bar chart of route lengths per driver
        if result.get("feasible") and routes_dict:
            st.subheader("Route length overview")
            lengths = {driver: len(stops) for driver, stops in routes_dict.items()}
            fig, ax = plt.subplots()
            ax.bar(lengths.keys(), lengths.values())
            ax.set_xlabel("Driver")
            ax.set_ylabel("Number of stops")
            ax.set_title("Stops per driver")
            st.pyplot(fig)
        else:
            st.info("Visualization omitted – solution not feasible or routes missing.")

# ---------------------------------------------------------------------------
# Entry point for ``streamlit run``
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _run_streamlit_app()
