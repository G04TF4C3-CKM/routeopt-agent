# Augmentation Runtime Diagnostics

## Metadata

- Task ID: `augmentation-runtime-diagnostics-v1`
- Date: `2026-07-24`
- Branch: `feat/augmentation-runtime-diagnostics`
- Repository: `git@github.com:G04TF4C3-CKM/routeopt-agent.git`
- Base commit: `ab1156d6ef7970a5243607252c0af97b560917b4`
- Red contract commit: `16f34ce4ba16dac0978d10f8e6c2c8a70af9fdfd`
- Green implementation commit: `4fd961a0fa335e57606b26c2c1b10fe683192d5b`
- Documentation commit: recorded by Git history after this file is committed
- Status: Complete
- Human reviewer: Casey Moffatt
- Agent implementation environment: Codex
- Mathematical solver internals modified: No

## Objective

This task added two complementary timing layers:

- the existing workflow runtime, which measures user-visible execution around
  the complete routing workflow;
- routing-engine phase and per-augmentation diagnostics, which provide
  engineering boundaries around setup, solver execution, successful
  augmentations, progress callbacks, termination work, and result finalization.

The result is a reproducible, benchmark-ready development instance, not a claim
that the repository contains a formal benchmark harness.

## Architectural decision

Option B was selected:

```text
Lightweight routing-engine orchestration instrumentation
```

Streamlit inter-callback intervals were rejected because they include work
outside one successful augmentation and omit the final unsuccessful search.
The existing discharge calls already formed stable boundaries around complete
attempted search-and-application operations. Deep search and application
instrumentation would have required editing the mathematical solver modules,
so that split was deferred.

## Commit sequence

1. The Red Team commit added deterministic executable acceptance contracts:
   `16f34ce4ba16dac0978d10f8e6c2c8a70af9fdfd` (`16f34ce`).
2. The Green Team commit implemented the accepted timing contract:
   `4fd961a0fa335e57606b26c2c1b10fe683192d5b` (`4fd961a`).
3. The documentation commit containing this record preserves the development
   provenance and is identified by subsequent Git history.

The Red contract was based on
`ab1156d6ef7970a5243607252c0af97b560917b4` (`ab1156d`).

## Preserved invariants

The phase preserved:

- Bellman-Ford path selection;
- Karp/MMC v1 firing-path behavior;
- Karp/MMC v2 source-rooted-cycle behavior;
- feasibility logic;
- residual and route mutation;
- iteration semantics;
- callback ordering;
- historical applied-walk sequences;
- final routes;
- driver counts;
- objective totals.

The following mathematical and workflow files were untouched:

```text
src/legacy_vrp.py
src/experimental_karp_mmc.py
src/agent_workflow.py
```

## Artifacts

- [Red Team prompt](red_team_prompt.md)
- [Red Team report](red_team_report.md)
- [Green Team prompt](green_team_prompt.md)
- [Green Team report](green_team_report.md)
- [Verification record](verification.md)

## Verification summary

- Red Team focused result: `20 failed, 43 passed, 22 skipped`
- Green Team focused result: `85 passed`
- Green Team full-suite result: `116 passed`

The Red Team result was intentional. Test collection succeeded, missing
production contracts failed visibly, and timing-dependent behavioral tests
remained gated until the clock seam and optional fields existed.

## Future extensions

The following items remain deferred:

- separate search and application timings;
- richer per-step route snapshots;
- explicit termination-reason contracts;
- timing progression charts after semantics stabilize;
- optional SQLite persistence;
- conversion of this task record into a replayable benchmark instance.
