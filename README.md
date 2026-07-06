# RouteOpt Agent

RouteOpt Agent is a Kaggle 5-Day Vibe Coding capstone backend that wraps a legacy vehicle-routing optimization experiment in a clean, agent-style workflow.

## Problem
Vehicle-routing optimization is operationally valuable but hard for non-experts to run and interpret. Dispatchers and analysts need tools that validate routing scenarios, run optimization logic, and explain the result in business language.

## Solution
This project takes a custom residual-graph VRP optimizer and exposes it through a minimal workflow:

```text
Load scenario -> Validate scenario -> Run optimizer -> Analyze result -> Explain result
```

## Course concepts demonstrated

- **Agent / workflow design:** the backend uses explicit workflow nodes and shared state in `src/agent_workflow.py`.
- **Security features:** inputs are local-only, URLs are rejected, no credentials are used, and the backend has no external side effects.
- **Spec-driven development:** project behavior and acceptance scenarios live in `specs/`.
- **Deployability path:** the current backend runs as a CLI and is ready to be wrapped in Streamlit, Gradio, or another lightweight app.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the sample scenario

```bash
python app.py data/sample_8_loads.txt --time-limit 12
```

## Streamlit Demo

```bash
streamlit run streamlit_app.py
```

The Streamlit app provides a simple UI to select a bundled scenario, set the driver time limit, and view the optimization results (driver counts, route times, feasibility, and a basic route‑length chart).

Expected summary:

```text
The optimizer reduced the plan from 8 drivers to 3 drivers...
```

## Run tests

```bash
pytest -q
```

## Repository structure

```text
app.py                         CLI entry point
src/agent_workflow.py           workflow nodes and state
src/routing_engine.py           stable wrapper around the legacy optimizer
src/legacy_vrp.py               patched legacy optimization experiment
src/scenario_loader.py          input parsing and validation
src/result_analyzer.py          metrics and natural-language summary
data/                          sample routing scenarios
specs/                         capstone spec and BDD scenarios
tests/                         backend tests
```

## Notes

The current solver starts with one driver per load and repeatedly applies feasible residual-graph discharges to combine routes while respecting a driver time limit. The legacy optimization code is intentionally isolated in `src/legacy_vrp.py`; new app and agent layers should call `solve_routing_problem()` rather than reaching into legacy internals.
