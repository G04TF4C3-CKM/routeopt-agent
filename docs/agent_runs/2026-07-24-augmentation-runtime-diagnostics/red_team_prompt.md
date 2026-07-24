# Red Team Prompt

> This is a normalized archival version of the instruction set used for the
> Red Team run. Formatting has been condensed for version control, but the
> acceptance semantics are preserved.

## 1. Mission

Create executable acceptance contracts for precise RouteOpt Agent backend,
solver-phase, and per-augmentation timing diagnostics. Do not modify production
code. The tests must distinguish workflow runtime, routing-engine phases,
successful augmentation runtime, callback runtime, cumulative solver runtime,
and termination-tail runtime.

## 2. Architectural decision

Use lightweight orchestration instrumentation in `src/routing_engine.py`.
Do not use Streamlit inter-callback intervals as augmentation timing. Treat the
existing calls to `discharge_bellmanford()` and `discharge_mmc()` versions 1 and
2 as boundaries around one complete attempted search-and-application
operation. Do not instrument or refactor the mathematical solver internals.

## 3. Authorized files

Create:

```text
tests/test_augmentation_runtime.py
```

Modify only as needed:

```text
tests/test_run_history.py
tests/test_runtime_interface.py
```

No production file, fixture, or historical expected path may change.

## 4. Future production timing contract

Every successful normalized result must provide exactly these timing keys:

```text
routing_engine_runtime_seconds
problem_setup_runtime_seconds
solver_runtime_seconds
progress_callback_runtime_seconds
termination_tail_runtime_seconds
result_finalization_runtime_seconds
```

It must also provide callback-independent `augmentation_records`. Each record
must contain:

```text
iteration
solver_phase
applied_path
current_driver_count
current_total_time
current_max_driver_time
augmentation_runtime_seconds
cumulative_solver_runtime_seconds
message
```

Record paths must correspond one-to-one and in order with
`result["applied_paths"]`. Solver iteration counts are not required to equal
the number of augmentation records.

`SolverProgress` must gain backward-compatible optional fields:

```text
solver_phase
augmentation_runtime_seconds
cumulative_solver_runtime_seconds
```

## 5. Solver phase values

Use these structural values, selected directly from the routing-engine branch:

```text
bellman_firing_path
karp_mmc_v1_firing_path
karp_mmc_v2_source_rooted_cycle
```

Do not infer phases from messages or walk shape.

## 6. Exact timing semantics

- Routing-engine runtime begins at entry to `solve_routing_problem()` and ends
  when the normalized result is ready.
- Problem setup begins at routing-engine entry and ends immediately before the
  selected solver branch.
- Solver runtime spans the selected solver branch and includes synchronous
  progress callbacks.
- Augmentation timing starts immediately before a discharge attempt.
- Only successful attempts create augmentation records.
- Augmentation completion occurs after the returned path is recorded and
  post-step driver count, total time, and maximum driver time are computed.
- Augmentation completion is captured before constructing or invoking the
  external progress callback.
- Callback runtime measures only synchronous callback invocation and is
  accumulated separately.
- Cumulative solver runtime runs from solver-phase start through successful
  augmentation completion. It may include earlier callbacks, failed attempts,
  phase transitions, and orchestration.
- Termination tail starts after the final successful callback returns and ends
  when the solver branch completes.
- A zero-success run assigns the entire solver phase to termination tail.
- Failed Karp/MMC v1 work before a successful v2 augmentation is not charged to
  the v2 augmentation.
- Result finalization starts after solver return and ends when final metrics,
  routes, timing, augmentation records, and the normalized payload are ready.

The contract must support approximate reconciliation without requiring a zero
bookkeeping remainder.

## 7. Deterministic clock strategy

Require a narrow module-level callable named `_monotonic_time` in
`src.routing_engine`. Tests must monkeypatch it with a `ManualClock` whose value
advances only when test wrappers explicitly advance it.

Do not add a public clock argument. Do not use `sleep()` or real-duration
thresholds. Where appropriate, wrap the real discharge helpers so historical
algorithm behavior remains exercised while durations remain synthetic.

## 8. Backend acceptance cases

Cover deterministic cases for:

1. one Bellman-Ford augmentation with an exact synthetic duration;
2. multiple Bellman-Ford augmentations with independent durations;
3. final unsuccessful Bellman-Ford search included in termination tail;
4. iteration-limit exit without a fabricated unsuccessful record;
5. zero successful augmentations;
6. common timing boundaries for Karp/MMC v1;
7. the exact `karp_mmc_v2_source_rooted_cycle` phase;
8. failed v1 work excluded from the successful v2 augmentation duration;
9. finite, nonnegative, monotone cumulative values;
10. callback runtime separated from augmentation runtime;
11. termination tail beginning after the final callback;
12. zero callback runtime when no callback is supplied;
13. unchanged paths, routes, driver counts, feasibility, and historical walks;
14. finite and nonnegative timing values;
15. callback-independent augmentation records;
16. one-to-one ordered correspondence between records and applied paths.

No separate search or application timing is required.

## 9. Run-history acceptance cases

Require `normalize_progress_event()` to:

- omit absent optional fields;
- preserve present structural and timing fields;
- copy and detach applied paths;
- convert timing values to floats;
- reject negative, NaN, and infinite timing values;
- remain serializable with `allow_nan=False`.

Require `build_run_record()` and history selection to preserve complete result
timing and augmentation records without mutation. Older records without
detailed timing must remain valid. The run-history schema version remains `1`.

## 10. Run Details acceptance cases

Use AST inspection rather than importing Streamlit. Require visible labels:

```text
Routing-engine runtime
Problem setup runtime
Solver runtime
Progress callback runtime
Solver logic runtime
Termination tail runtime
Result finalization runtime
Workflow outside routing engine
Solver bookkeeping remainder
```

The augmentation display must include:

```text
Solver phase
Augmentation runtime
Cumulative solver runtime
```

Require the fallback:

```text
Detailed solver timing was not captured for this run.
```

Protect the derived subtraction formulas and reject silent clamping of a
materially negative bookkeeping remainder. Preserve the existing navigation
contracts proving that opening details does not rerun the workflow.

## 11. Scope exclusions

Exclude:

- separate search and application timing;
- individual relaxation or edge timing;
- timing charts;
- DOM or network timing;
- SQLite and persistence;
- caching;
- performance thresholds.

Do not modify `src/legacy_vrp.py`, `src/experimental_karp_mmc.py`, solver
dataclasses, run-history production code, Streamlit, algorithms, fixtures, or
historical expected paths during the Red Team run.

## 12. Required verification

Show the complete authorized test diff, run `git diff --check`, and run only:

```bash
pytest -q -vv \
  tests/test_augmentation_runtime.py \
  tests/test_run_history.py \
  tests/test_runtime_interface.py
```

Collection must succeed. Existing regressions must remain green. New
production-contract checks must fail until Green Team implementation exists,
and timing-dependent behavioral checks may remain feature-gated.
