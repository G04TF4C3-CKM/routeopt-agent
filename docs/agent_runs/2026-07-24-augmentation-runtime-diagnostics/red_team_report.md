# Red Team Report

> Curated from the committed acceptance tests and verified Git history. This is
> not a verbatim agent transcript.

## Commit

The Red Team contract is anchored by
`16f34ce4ba16dac0978d10f8e6c2c8a70af9fdfd`, with subject
`Add augmentation runtime diagnostic contracts`.

## Changed tests

```text
tests/test_augmentation_runtime.py
tests/test_run_history.py
tests/test_runtime_interface.py
```

## Test design

- Import and feature gating prevented collection errors before the production
  clock seam and optional progress fields existed.
- `ManualClock` supplied deterministic durations advanced only by test
  wrappers.
- Real Bellman-Ford and Karp/MMC discharge helpers were wrapped where
  appropriate so historical path behavior remained exercised.
- No `sleep()` call or execution-time threshold was used.
- AST tests protected exact interface labels, derived formulas, the
  older-record fallback, and navigation behavior.
- Run-history tests protected strict JSON serialization, detached path
  snapshots, optional-field behavior, and backward compatibility.

## Red verification

```text
20 failed, 43 passed, 22 skipped
```

This was the intentional Red state. Collection succeeded. Failures represented
the missing production clock seam, progress fields, result timing contract, and
Run Details presentation. Timing-dependent tests activated automatically only
after the clock seam or optional fields became available.

## Scope

No production file changed in the Red Team commit. The commit added
`tests/test_augmentation_runtime.py` and modified only
`tests/test_run_history.py` and `tests/test_runtime_interface.py`.
