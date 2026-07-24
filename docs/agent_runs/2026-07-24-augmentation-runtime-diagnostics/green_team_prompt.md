# Green Team Prompt

> This is a normalized archival version of the instruction set used for the
> Green Team run. Formatting has been condensed for version control, but the
> implementation boundaries and timing semantics are preserved.

## 1. Mission

Implement only the production changes needed to satisfy the committed
augmentation-runtime acceptance contracts. Add precise routing-engine,
solver-phase, callback, termination-tail, and per-successful-augmentation
diagnostics without changing mathematical behavior.

## 2. Authorized production files

```text
src/routing_engine.py
src/solver_types.py
src/run_history.py
streamlit_app.py
```

## 3. Prohibited files

```text
src/legacy_vrp.py
src/experimental_karp_mmc.py
src/agent_workflow.py
src/ui_utils.py
tests/**
```

Do not change fixtures, historical path expectations, solver selection,
feasibility logic, residual or route mutation, iteration semantics,
persistence, or caching.

## 4. Clock seam

Expose a module-level `_monotonic_time` callable in `src/routing_engine.py`
using a monotonic high-resolution production clock such as
`time.perf_counter()`. All new routing-engine timing must use this seam. Do not
add a clock argument to the public API.

Elapsed intervals must be finite and nonnegative. Do not silently clamp a
negative captured interval.

## 5. `SolverProgress` extension

Append these optional fields with `None` defaults:

```text
solver_phase
augmentation_runtime_seconds
cumulative_solver_runtime_seconds
```

Existing constructors must remain valid. New routing-engine events must
populate all three fields.

## 6. Result timing contract

Every successful result must contain a `timing` dictionary with exactly:

```text
routing_engine_runtime_seconds
problem_setup_runtime_seconds
solver_runtime_seconds
progress_callback_runtime_seconds
termination_tail_runtime_seconds
result_finalization_runtime_seconds
```

Routing-engine runtime spans entry through a ready normalized result. Problem
setup ends immediately before the selected solver branch. Solver runtime spans
that branch and includes synchronous callbacks. Result finalization begins
after the solver branch and covers final routes, metrics, feasibility, records,
timing data, and normalized result construction.

## 7. Augmentation-record contract

Every successful result must contain `augmentation_records`, even without a
progress callback. Each successful record must contain:

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

Use fresh path lists. Preserve order and one-to-one correspondence with
`result["applied_paths"]`. Do not equate iteration count with record count.

Use exact structural phases:

```text
bellman_firing_path
karp_mmc_v1_firing_path
karp_mmc_v2_source_rooted_cycle
```

Start an attempt timer immediately before each discharge helper. Create a
record only when a walk succeeds. Capture completion after path recording and
post-step driver, total-time, and maximum-time metrics, but before progress
event construction or callback invocation.

## 8. Callback timing

Measure only synchronous invocation of the supplied callback:

```text
callback start
    → callback invocation
callback end
```

Accumulate that interval separately. Event construction, record construction,
and path copying are not callback runtime. Without a callback, callback runtime
must be `0.0`.

## 9. Termination-tail semantics

For a successful augmentation, record the final-success boundary after its
callback returns. Without a callback, record the boundary after event and
record bookkeeping. Termination tail spans that boundary through solver-branch
completion.

For zero successes, termination tail equals total solver runtime. It includes
final unsuccessful attempts, stopping-condition evaluation, iteration-limit
exit work, and solver cleanup, but excludes the final successful callback.

## 10. Bellman-Ford preservation requirements

Preserve pre-attempt iteration increments, unsuccessful final-attempt
semantics, paths, routes, metrics, and callback ordering. Successful events use:

```text
solver_phase: bellman_firing_path
message: discharge applied
```

Keep the existing `vrp.discharge_bellmanford()` call unchanged.

## 11. Karp/MMC preservation requirements

Preserve repeated version-1 attempts followed, when allowed, by at most one
version-2 source-rooted-cycle attempt. Failed version-1 work before a successful
version-2 augmentation must remain outside the v2 augmentation duration and
inside cumulative or bookkeeping time.

Use:

```text
karp_mmc_v1_firing_path
karp_mmc_v2_source_rooted_cycle
```

Keep both existing `karp_discharge()` helper calls and their algorithmic
behavior unchanged.

## 12. Run-history behavior

Extend the progress-event typed contract with optional structural and timing
keys. `normalize_progress_event()` must omit absent fields, copy present
fields, convert timings to floats, and reject negative, NaN, or infinite
values. Paths and nested results must remain detached and JSON-safe.

Preserve complete result timing and augmentation records through
`build_run_record()`. Keep schema version `1`. Older records without detailed
timing remain valid.

## 13. Run Details presentation

Leave the manager summary unchanged. For complete timed records, visibly show:

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

Derive solver logic, workflow-outside-routing-engine, and solver bookkeeping
values by subtraction. Treat tolerance-level negative display noise as zero,
but warn and preserve materially negative values.

Build the ordered augmentation table from `result["augmentation_records"]`
with:

```text
Step
Solver phase
Applied walk
Driver count
Total route time
Maximum route time
Augmentation runtime
Cumulative solver runtime
Message
```

Use the existing runtime formatter. Add a concise timing-semantics note. Do not
add a chart or claim separate search and application timing.

## 14. Backward compatibility

For older records without the complete timing contract, display exactly:

```text
Detailed solver timing was not captured for this run.
```

Continue rendering all existing details. Preserve session history,
selected-run behavior, callback-driven navigation, workflow runtime, raw
normalized results, route comparison, progress status, and error handling.

## 15. Verification requirements

Show the complete authorized production diff and run:

```bash
git diff --check
pytest -q -vv \
  tests/test_augmentation_runtime.py \
  tests/test_run_history.py \
  tests/test_runtime_interface.py
pytest -q
```

Expected results:

```text
85 passed
116 passed
```

Only the four authorized production files may change. Do not stage or commit
during the implementation run.
