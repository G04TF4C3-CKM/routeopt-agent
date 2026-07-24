# Agent-Run Records

## Purpose

Agent-run records preserve architectural intent, acceptance contracts,
implementation scope, verification evidence, and commit ancestry for substantial
agent-assisted changes.

## When to create a record

Use this structure for changes involving:

- algorithms;
- architecture;
- data contracts;
- safety boundaries;
- persistent schemas;
- instrumentation semantics;
- major interface workflows;
- difficult regressions.

It is not required for trivial copy edits or mechanical cleanup.

## Standard sequence

```text
Red Team contract
    → failing executable acceptance tests

Green Team implementation
    → production changes that satisfy the contract

Author/Provenance pass
    → durable record linking intent, evidence, and commits
```

“Author/Provenance pass” is the preferred repository label. The work can be
described as purple-style reconciliation, but it is not a security Purple Team
exercise.

## Recommended task directory

Each task directory should contain:

```text
README.md
red_team_prompt.md
red_team_report.md
green_team_prompt.md
green_team_report.md
verification.md
```

## Current records

- [Augmentation Runtime Diagnostics](2026-07-24-augmentation-runtime-diagnostics/)
