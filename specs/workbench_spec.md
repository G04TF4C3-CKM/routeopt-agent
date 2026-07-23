# RouteOpt Agent Workbench Specification

## Purpose

RouteOpt Agent is a personal algorithm-engineering workbench for constrained
vehicle routing, residual-graph augmentation experiments, solver comparison,
diagnostics, and future agent-assisted analysis.

The workbench exposes deterministic routing algorithms through shared input,
validation, result, and presentation boundaries. It is intended for
reproducible experimentation and does not claim global optimality or production
readiness.

## Inputs

The CLI and Python API accept a readable local scenario file with one
pickup-and-dropoff pair per line:

```text
(pickup_x, pickup_y), (dropoff_x, dropoff_y)
```

The Streamlit interface supports:

- bundled local scenario files;
- uploaded TXT files in the coordinate-pair format;
- uploaded CSV files with the header
  `pickup_x,pickup_y,dropoff_x,dropoff_y`;
- manual coordinate-pair or numbered-tuple input.

Uploaded and manually entered rows are parsed and normalized into a temporary
local scenario before routing begins.

## Validation and constraints

- Inputs must resolve to readable local files; remote URL-shaped paths are
  rejected.
- Scenario rows must contain valid numeric pickup and dropoff coordinates.
- Empty scenarios and scenarios over the configured load-count limit are
  rejected.
- Streamlit uploads are restricted by file type and size before parsing.
- Every solver run receives a driver time limit.
- A result is feasible only when no driver remains over the limit and the
  maximum route time is within that limit.

Validation failures must be reported without presenting a successful solver
result.

## Application workflow

```text
load local scenario
    -> validate scenario
    -> select and run solver
    -> analyze feasibility and route-time results
    -> explain and present the result
```

`src/agent_workflow.py` coordinates these stages for both application
interfaces and remains a natural integration point for future agent-assisted
interaction.

## Solver modes

### Stable Bellman-Ford discharge

`bellman_discharge` is the stable baseline. It repeatedly applies feasible
Bellman-Ford firing-path discharges through the preserved residual-graph
implementation while respecting the configured driver time limit.

### Experimental Karp/MMC discharge

`karp_mmc` is experimental. The current public solver workflow:

1. exhausts version-1 firing-path discharges, subject to the iteration limit;
2. if iteration budget remains, attempts at most one source-rooted version-2
   augmentation.

Central-cycle decomposition, sink-rooted search, robust compound-walk handling,
and broader pivot-selection logic remain deferred. The experimental mode must
not be presented as complete or globally optimal.

## Result contract and diagnostics

`src.routing_engine.solve_routing_problem()` returns a normalized result for
both solver modes. The result includes:

- scenario and validation information;
- configured time limit and iteration information;
- initial and final driver counts;
- initial and final routes;
- initial and final total route time;
- maximum driver time and feasibility;
- applied augmentation walks;
- the last reported cycle or walk;
- iteration-limit termination status.

Callers may provide a `progress_callback` to receive `SolverProgress` snapshots
after successful augmentations.

## Access surfaces

- `app.py` provides CLI access to the stable default workflow and optional JSON
  result output.
- `streamlit_app.py` provides bundled, uploaded, and manual input; solver-mode
  selection; progress updates; metrics; route presentation; and Agent Trace.
- `solve_routing_problem()` provides direct Python access to both solver modes.

All access surfaces must preserve the same routing, validation, and feasibility
semantics for equivalent inputs and configuration.

## Determinism and safety boundaries

- Solver execution remains local and deterministic for the same code, input,
  and configuration.
- No credentials or external services are required.
- Routing execution performs no email, database, upload, or cloud side effects.
- Input parsing, workflow orchestration, solver dispatch, and result analysis
  remain separated from algorithm internals.
- Future agent-assisted behavior must consume validated solver results without
  silently changing algorithm state or historical regression expectations.

## Testability and success criteria

- The stable Bellman-Ford baseline remains protected by focused and full-suite
  regression tests.
- The sample eight-load scenario with a driver time limit of `12.0` reduces
  from eight initial drivers to three final drivers while remaining feasible.
- The experimental Karp/MMC path remains covered by smoke tests and historical
  fixtures without implying that deferred search branches are implemented.
- Invalid local inputs and remote URL-shaped paths are rejected before a
  successful result is presented.
- Focused tests and the complete suite must pass for changes to active behavior.
