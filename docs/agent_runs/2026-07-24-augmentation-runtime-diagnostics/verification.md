# Verification

## Environment assumptions

- This is a Python project using the existing repository `.venv`.
- Tests are run with `pytest`.
- The committed timing tests reference `data/sample_8_loads.txt` and
  `tests/fixtures/loads_5_8_hiring_firing_path.txt`.
- Detached reproduction should be performed only in a clean worktree, a
  separate worktree, or a disposable clone.

No untracked operating-system package versions, dependency versions, model
versions, token counts, costs, or development durations are asserted here.

## Commit ancestry

```text
ab1156d6ef7970a5243607252c0af97b560917b4
    ↓
16f34ce4ba16dac0978d10f8e6c2c8a70af9fdfd
    Add augmentation runtime diagnostic contracts
    ↓
4fd961a0fa335e57606b26c2c1b10fe683192d5b
    Instrument augmentation runtime diagnostics
    ↓
documentation commit
```

## Red Team reproduction

From a detached worktree, disposable clone, or temporary branch with no
uncommitted changes:

```bash
git switch --detach 16f34ce4ba16dac0978d10f8e6c2c8a70af9fdfd
pytest -q -vv \
  tests/test_augmentation_runtime.py \
  tests/test_run_history.py \
  tests/test_runtime_interface.py
```

Expected historical result:

```text
20 failed, 43 passed, 22 skipped
```

This command intentionally returns a failing exit status because it reproduces
the Red Team state before production implementation.

## Green Team reproduction

From a detached worktree, disposable clone, or temporary branch with no
uncommitted changes:

```bash
git switch --detach 4fd961a0fa335e57606b26c2c1b10fe683192d5b
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

## Contract checks

The committed deterministic tests verify:

- exact synthetic runtime for one successful augmentation;
- independent durations for multiple augmentations;
- monotone cumulative solver runtime;
- callback exclusion from augmentation runtime and separate callback totals;
- termination tail beginning after the final successful callback;
- complete solver-phase assignment to termination tail for zero successes;
- Karp/MMC v1 and v2 structural phase separation;
- exclusion of failed v1 work from a successful v2 augmentation duration;
- preservation of historical paths, final routes, driver counts, and
  feasibility;
- finite, nonnegative timing values and approximate reconciliation;
- callback-independent augmentation records;
- JSON-safe, detached run-history preservation and legacy compatibility;
- Run Details labels, derived formulas, inconsistency warnings, fallback, and
  callback-driven navigation.

## Manual verification

Manual Streamlit verification is not recorded in this provenance commit.

Manual Streamlit verification was performed by the human reviewer outside the
automated test suite only if separately recorded in the task README or PR.

## Known limitations

- Wall-clock timings naturally vary between executions and environments.
- Tests verify timing boundaries with a deterministic clock, not performance
  speed.
- Search and application are not separately timed.
- Callbacks remain part of solver wall runtime but are separately measured.
- Detailed timing is absent from pre-instrumentation history records.
- History remains session-local rather than SQLite-backed.
