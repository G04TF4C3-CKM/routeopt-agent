# Green Team Report

> Curated from the committed implementation, acceptance tests, and verified Git
> history. This is not a verbatim agent transcript.

## Commit

The Green Team implementation is anchored by
`4fd961a0fa335e57606b26c2c1b10fe683192d5b`, with subject
`Instrument augmentation runtime diagnostics`.

## `src/routing_engine.py`

- Added the `_monotonic_time` seam backed by a monotonic high-resolution
  production clock.
- Added validation for finite, nonnegative elapsed intervals and accumulated
  runtime.
- Captured problem setup, total solver, callback, termination-tail, result
  finalization, and total routing-engine timings.
- Created callback-independent augmentation records after post-step metrics
  and before callback execution.
- Assigned structural phases for Bellman-Ford, Karp/MMC v1, and Karp/MMC v2.
- Kept the existing Bellman-Ford and Karp/MMC discharge/helper calls unchanged.

## `src/solver_types.py`

Added three optional, backward-compatible `SolverProgress` fields:

```text
solver_phase
augmentation_runtime_seconds
cumulative_solver_runtime_seconds
```

## `src/run_history.py`

- Added optional typed timing fields to progress-event records.
- Validated timing values as finite and nonnegative.
- Preserved detached, strictly JSON-safe snapshots.
- Kept the run-history schema version at `1`.

## `streamlit_app.py`

- Added the detailed routing-engine and solver timing overview.
- Added the ordered augmentation timing table.
- Added the explicit legacy-record fallback.
- Added derived remainder calculations and warnings for materially negative,
  inconsistent values.
- Added a concise timing-semantics note.
- Did not add a timing chart.
- Left the manager-facing summary unchanged.

## Verification

```text
Focused timing/history/interface suite: 85 passed
Full suite: 116 passed
```

The focused suite covered deterministic clock boundaries, event and history
contracts, interface formulas, and navigation. The full suite confirmed
compatibility with the repository's existing behavior.

## Scope confirmation

No tests, fixtures, mathematical solver modules, or workflow orchestration
module changed in the Green Team commit. The commit modified only:

```text
src/routing_engine.py
src/solver_types.py
src/run_history.py
streamlit_app.py
```
