# RouteOpt Agent

RouteOpt Agent is a personal algorithm-engineering workbench for constrained
vehicle routing, residual-graph augmentation experiments, solver comparison,
diagnostics, and future agent-assisted analysis.

The project preserves a working Bellman-Ford baseline while developing and
testing an experimental Karp/minimum-mean-cycle (MMC) alternative. It provides
reproducible routing scenarios, a shared solver API, feasibility and route-time
validation, a command-line interface, and an interactive Streamlit interface.
The algorithms remain research-oriented: experimental results are reported as
such, and the project does not claim global optimality or production readiness.

## Current capabilities

- Load and validate reproducible pickup-and-dropoff routing scenarios.
- Run the stable `bellman_discharge` baseline, which applies feasible
  Bellman-Ford firing-path discharges to combine driver routes.
- Run the experimental `karp_mmc` path for comparison and diagnostics.
- Compare initial and final driver counts, route times, feasibility, applied
  augmentations, iteration counts, and termination status.
- Observe successful augmentations through the `SolverProgress` callback.
- Use the same deterministic workflow from the CLI and Streamlit interfaces.
- Keep solver execution local and deterministic so a future agentic layer can
  explain results, ask clarifying questions, and support comparative analysis.

## Solver maturity

### Bellman-Ford discharge

`bellman_discharge` is the stable baseline. It wraps the preserved residual-graph
and Bellman-Ford discharge routine in `src/legacy_vrp.py` and repeatedly applies
feasible firing paths while respecting the configured driver time limit.

### Experimental Karp/MMC

`karp_mmc` is an experimental extraction of the historical Karp/MMC work. In
the validated public workflow, it exhausts version-1 firing-path discharges and
then attempts at most one source-rooted version-2 residual-cycle augmentation
per solver call.

This path does not yet reproduce every branch explored in the historical
notebooks. Central-cycle decomposition, sink-rooted search, robust
compound-walk handling, and broader pivot-selection logic remain backend
research tasks.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Input format

CLI scenario files contain one pickup-and-dropoff pair per line:

```text
(pickup_x, pickup_y), (dropoff_x, dropoff_y)
```

For example:

```text
(1.0, 2.0), (3.0, 4.0)
(2.0, 1.0), (4.0, 3.0)
```

The Streamlit interface also accepts manual input, numbered tuple rows, and CSV
uploads with this header:

```text
pickup_x,pickup_y,dropoff_x,dropoff_y
```

## CLI usage

Run the stable baseline on a bundled scenario:

```bash
python app.py data/sample_8_loads.txt --time-limit 12
```

Use `--json` to print the complete normalized result:

```bash
python app.py data/sample_8_loads.txt --time-limit 12 --json
```

## Streamlit usage

```bash
streamlit run streamlit_app.py
```

The interface supports bundled scenarios, local TXT or CSV uploads, and manual
entry. Users can choose the stable Bellman-Ford baseline or the experimental
Karp/MMC path, configure route-time units and the driver limit, monitor progress,
and inspect feasibility, route-time metrics, final routes, and the Agent Trace.

## Public solver API

The shared backend entry point is `solve_routing_problem()` in
`src/routing_engine.py`:

```python
from src.routing_engine import solve_routing_problem

result = solve_routing_problem(
    "data/sample_8_loads.txt",
    time_limit=12.0,
    solver_mode="bellman_discharge",
)
```

Supported solver modes are:

- `bellman_discharge` — stable default;
- `karp_mmc` — experimental Karp/MMC discharge.

The optional `progress_callback` receives `SolverProgress` snapshots after
successful augmentations. Results include initial and final routes, driver
counts, total and maximum route times, feasibility, applied paths, iteration
information, and validation details.

## Safety and validation

- Remote URLs are rejected; solver inputs must be readable local files.
- Scenario rows and load counts are validated before solver execution.
- Streamlit uploads are size-limited and parsed before a temporary local
  scenario is created.
- The application does not require credentials or external services.
- Solver execution has no email, database, upload, or cloud side effects.

## Tests

```bash
pytest -q
```

The suite covers scenario parsing, custom input handling, solver dispatch,
workflow behavior, Streamlit helpers, and historical Karp/MMC regression cases.

## Repository structure

```text
app.py                           CLI entry point
streamlit_app.py                 interactive workbench
src/agent_workflow.py            deterministic workflow orchestration
src/routing_engine.py            shared solver dispatch and normalized results
src/legacy_vrp.py                preserved Bellman-Ford baseline internals
src/experimental_karp_mmc.py     experimental Karp/MMC extraction
src/solver_types.py              shared progress structures
src/scenario_loader.py           scenario parsing and validation
src/custom_input.py              Streamlit TXT/CSV/manual input parsing
src/result_analyzer.py           metrics and user-facing explanations
data/                            bundled routing scenarios
docs/                            architecture and project documentation
specs/                           behavioral specifications
tests/                           unit and regression tests
```

## Direction

RouteOpt Agent is intended to grow into a comparative routing-algorithm
workbench with richer augmentation diagnostics, pivot-sequence analysis,
additional solver strategies, optional distance-graph preprocessing, and
agent-assisted interaction built on top of deterministic solver results.
