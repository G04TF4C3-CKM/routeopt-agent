# RouteOpt Agent Architecture

RouteOpt Agent separates input handling, workflow orchestration, solver
execution, result analysis, and presentation so that the routing algorithms can
remain deterministic and independently testable.

## Application flow

```text
scenario file, upload, or custom input
    -> workflow orchestration
    -> routing engine
    -> selected solver
    -> feasibility and result analysis
    -> CLI or Streamlit presentation
```

The CLI reads an existing local scenario file. The Streamlit interface can use
a bundled scenario, validate an uploaded TXT or CSV file, or normalize manual
input into a temporary local scenario. Both interfaces call
`src.agent_workflow.run_routing_workflow()`.

## Module boundaries

- `app.py` provides the command-line interface.
- `streamlit_app.py` provides interactive input controls, progress display,
  metrics, the Agent Trace, route tables, and a small route-length chart.
- `src/custom_input.py` parses and normalizes Streamlit uploads and manual
  input.
- `src/scenario_loader.py` parses scenario rows and validates the load count.
- `src/safety.py` rejects remote URLs and unreadable local paths.
- `src/agent_workflow.py` coordinates loading, validation, optimization,
  analysis, and explanation.
- `src/routing_engine.py` exposes `solve_routing_problem()`, dispatches to the
  selected solver, and returns normalized results.
- `src/legacy_vrp.py` contains the preserved Bellman-Ford routing baseline and
  shared residual-graph domain structures.
- `src/experimental_karp_mmc.py` contains the experimental Karp/MMC extraction.
- `src/result_analyzer.py` derives comparison metrics and a user-facing
  explanation from the normalized solver result.
- `src/solver_types.py` defines progress snapshots shared by solver callers.

## Workflow orchestration

`run_routing_workflow()` executes the deterministic application stages in
order:

```text
load scenario
    -> validate scenario
    -> run selected solver
    -> analyze solution
    -> explain solution
```

An invalid or unreadable input stops the workflow before a solver result is
presented. The workflow converts errors into `WorkflowState.errors` for CLI or
Streamlit handling.

This module is also the natural integration point for future agentic behavior.
An interactive agent can eventually interpret constraints, compare solver
results, explain augmentations, or prepare reports while leaving solver
execution reproducible and testable.

## Solver dispatch and normalized results

`routing_engine.solve_routing_problem()` validates the requested solver mode,
constructs the routing graph and initial one-driver-per-load solution, invokes
the selected solver, and reports a shared result structure.

The result includes:

- initial and final driver counts and routes;
- initial and final total route time;
- maximum driver time and feasibility;
- applied augmentation walks;
- iteration and termination information;
- the last reported cycle or walk;
- scenario-validation details.

The optional `progress_callback` receives a `SolverProgress` snapshot after
each successful augmentation.

## Solver paths

### Stable Bellman-Ford discharge

The default `bellman_discharge` mode repeatedly calls the preserved
Bellman-Ford residual discharge routine. Each accepted firing path updates the
driver solution while respecting the configured time limit. This is the stable
behavioral baseline and is protected by regression tests.

### Experimental Karp/MMC discharge

The `karp_mmc` mode uses the experimental minimum-mean-cycle extraction. A
public solver call currently:

1. repeats version-1 firing-path discharge until no path remains or the
   iteration limit is reached; then
2. if the iteration budget remains, attempts at most one source-rooted
   version-2 augmentation.

This boundary is intentionally narrower than the historical notebook
architecture. Compound walks with embedded central cycles, central-cycle
decomposition, sink-rooted search, and broader pivot-selection logic remain
deferred backend work. The experimental path should not be interpreted as a
global-optimality guarantee.

## Validation and safety

Input processing is local and deterministic:

- remote URL-shaped paths are rejected;
- missing or unreadable scenario files are rejected;
- malformed rows and excessive load counts fail validation;
- Streamlit uploads are size-limited and parsed before solver execution;
- no credentials or external services are required;
- solver execution performs no external messaging, database, or cloud actions.

Keeping these checks outside the algorithm internals lets both solver paths
share the same application boundary without forcing their internal residual
search architectures to be identical.
