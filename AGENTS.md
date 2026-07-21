# AGENTS.md

## Project purpose

This repository is an algorithm-engineering workbench for constrained vehicle routing.

It serves two purposes:

1. A technical interface for comparing routing and optimization algorithms.
2. A portfolio-quality demonstration for hiring managers and recruiters.

The long-term architecture should support:

- multiple routing solvers;
- common solver inputs and outputs;
- reproducible benchmark scenarios;
- algorithm diagnostics and traces;
- preprocessing strategies;
- later integration with a separate distance-graph backend.

The immediate priority is to make the existing Bellman-Ford and Karp/MMC approaches correct, testable, and comparable.

---

## Current technical priorities

Work in this order unless the human explicitly changes the priority:

1. Preserve the currently working Bellman-Ford implementation.
2. Recover the historical Karp/MMC behavior from the archived notebooks.
3. Convert historical notebook outputs into regression fixtures and tests.
4. Repair the production Karp/MMC implementation.
5. Normalize both solvers behind the same public API.
6. Expose solver comparison and diagnostics in the Streamlit interface.
7. Improve project naming, documentation, presentation, and video materials.
8. Add preprocessing and additional algorithms later.

Do not begin broad refactors while a smaller regression-driven repair is available.

---

## Important repository areas

### Production code

- `src/legacy_vrp.py`
  - Legacy routing structures and Bellman-Ford logic.
  - Treat as working baseline code.
  - Avoid unnecessary rewrites.

- `src/experimental_karp_mmc.py`
  - Current incomplete Karp/MMC extraction.
  - Do not assume it faithfully represents the archived notebooks.

- `src/routing_engine.py`
  - Public solver dispatch and normalized result handling.

- `src/solver_types.py`
  - Shared solver contracts and result structures.

- `src/agent_workflow.py`
  - Agent-facing orchestration logic.

- `streamlit_app.py`
  - User interface.

### Historical algorithm sources

Important historical material includes:

- `legacy_audit/KarpsMeanMinCycle_2.ipynb`
- other historical notebooks and source material in archived directories;
- the later optimality and hiring/reconnection-cycle experiments.

Historical notebooks are algorithm specifications and development evidence. Do not modify or delete them unless explicitly instructed.

When production behavior conflicts with a historical notebook, investigate the discrepancy before changing the expected regression behavior.

### Tests

Important test locations include:

- `tests/`
- `tests/fixtures/`

Historical scenarios should become committed fixtures with documented expected behavior.

---

## Engineering approach

Use a regression-first workflow.

Before modifying an algorithm:

1. Identify a reproducible input scenario.
2. Record the historically expected behavior.
3. Create a focused regression or smoke test.
4. Confirm that the current implementation fails for the expected reason.
5. Make the smallest production change that advances the test.
6. Run focused tests.
7. Run the full test suite.
8. Review the diff before committing.

Prefer small, reviewable changes over large rewrites.

Do not combine algorithm repair, interface redesign, file renaming, and documentation restructuring in one change.

---

## Agent workflow

Before editing:

1. Read this file.
2. Inspect the relevant production files, tests, fixtures, and historical sources.
3. Explain the discrepancy or requested task in concrete terms.
4. Propose a bounded implementation plan.
5. Wait for approval when the requested change is architectural or broad.

When editing:

- change only files required for the approved task;
- preserve public behavior unless the task explicitly changes it;
- do not silently alter historical oracle values;
- do not weaken tests merely to obtain a passing suite;
- avoid speculative abstractions;
- preserve useful comments that explain algorithmic intent.

After editing, report:

- every changed file;
- the reason for each change;
- any assumptions made;
- the exact verification commands;
- any unresolved risk or ambiguity.

---

## Command execution

The Antigravity command runner may fail with errors such as:

```text
CORTEX_STEP_TYPE_RUN_COMMAND
recvmsg: connection reset by peer
```

If a trivial command fails because of the command runner:

1. Do not repeatedly retry the same command.
2. Do not reinterpret it as a Python, package, virtual-environment, Git, or project failure.
3. Continue using file-inspection and file-editing tools when possible.
4. Provide the exact command for the human operator to run manually.
5. Wait for the human to paste the result.

The integrated terminal or an external terminal may still work even when the agent command runner fails.

Do not spend tokens repeatedly testing `echo`, `pwd`, or equivalent probes after the runner failure has been established.

---

## Python environment

This repository uses the existing project-local virtual environment:

```bash
source .venv/bin/activate
```

Do not create a second virtual environment unless explicitly instructed.

Do not replace the environment with Conda, Poetry, Pipenv, or another package manager.

Install dependencies only when necessary and only through the existing project environment.

Typical verification commands:

```bash
source .venv/bin/activate
pytest -q
```

Focused test example:

```bash
pytest -q -rxX tests/test_historical_karp_smoke.py
```

---

## Testing rules

Tests should verify meaningful behavior, not merely that an API accepts a solver name.

For solver work, prefer assertions on:

- feasibility;
- initial and final driver counts;
- objective values;
- route validity;
- augmentation types;
- applied paths or cycles;
- runtime and termination status;
- invariant preservation.

Use `xfail(strict=True)` only for a known, documented missing behavior.

An unexpected pass should trigger review and deliberate removal or revision of the marker.

Do not convert a failing behavioral test into a no-op acceptance test.

Do not update historical expected values unless the human confirms that the historical oracle was incorrect.

---

## Karp/MMC-specific guidance

The archived Karp work represents a richer architecture than the older Bellman-Ford implementation.

Important concepts may include:

- firing paths from `-1` to `0`;
- negative cycles through `0`;
- reconnection or hiring cycles;
- alternating edge additions and deletions;
- multiple feasible labels reaching the same residual vertex;
- candidate-specific `Drivers` states;
- residual feasibility during augmentation.

Do not reduce these concepts to a single scalar distance or a single predecessor per vertex without proving that the reduction is valid.

Separate these concerns where practical:

```text
find augmentation
validate augmentation
apply augmentation
record diagnostics
```

Do not assume every returned walk is a cycle. Use explicit augmentation types.

The historical notebook work should be treated as the behavioral specification until the behavior has been deliberately reproduced and validated in production code.

---

## Architecture direction

The internal architectures of Bellman-Ford and Karp/MMC may remain different.

They should eventually share a normalized external contract such as:

```text
problem input
solver configuration
solver result
validation
metrics
diagnostics
```

Avoid forcing Karp/MMC into Bellman-Ford internals merely to reuse code.

Reuse domain structures only when their semantics are genuinely compatible.

Future preprocessing, including distance-graph preprocessing, should remain separate from individual solver implementations.

Conceptual pipeline:

```text
problem instance
    -> optional preprocessing
    -> selected solver
    -> normalized result
    -> validation
    -> metrics and analysis
    -> interface
```

---

## Current historical regression target

The immediate regression target is the archived hiring/firing-path scenario.

The historical behavior includes:

- an initial five-driver solution;
- three firing-path augmentations;
- reduction to two drivers;
- a later hiring/reconnection augmentation found by the more mature notebook implementation;
- preservation of feasibility;
- no remaining applicable negative augmentation under the historical optimality checks.

The regression fixture and smoke test should document this behavior without modifying production solver code.

The smoke test may initially use `xfail(strict=True)` to represent known missing production behavior.

Do not change the historical oracle merely because the current production implementation fails to reproduce it.

---

## Git safety

Before editing, inspect:

```bash
git status
git branch --show-current
```

Do not:

- work directly on `main` for a substantial task;
- force-push;
- rewrite history;
- delete branches;
- discard uncommitted work;
- run destructive Git commands;
- commit generated caches or temporary task files.

Use focused branches such as:

```text
test/historical-karp-smoke
fix/karp-firing-path
fix/karp-reconnection-cycle
refactor/solver-result-contract
ui/solver-comparison
```

Do not commit temporary files such as `_agy_task.patch`.

The human operator performs final review, commit, push, and merge unless explicitly delegated.

---

## Code quality

Use:

- clear names;
- type hints where they improve understanding;
- small functions with explicit responsibilities;
- dataclasses for structured results;
- comments for non-obvious mathematical or residual-graph logic;
- deterministic behavior where practical.

Avoid:

- broad exception swallowing;
- hidden global state;
- unexplained magic constants;
- duplicate solver logic;
- premature generalization;
- cosmetic rewrites unrelated to the task;
- overstating correctness or optimality.

When an algorithm is experimental, label it accurately.

When optimality is not proved, do not describe the result as optimal.

---

## Documentation and presentation

Preserve the useful presentation structure:

- `README.md`
- `docs/architecture.md`
- `docs/video_script.md`
- project write-up materials
- the Streamlit interface

Course-specific names may be changed later, but renaming should be performed separately from algorithm repair.

Documentation should distinguish:

- working behavior;
- historical behavior;
- experimental behavior;
- planned architecture;
- verified results;
- conjectures and future research.

The eventual project should support both:

1. A manager-facing demonstration of solver behavior and results.
2. An algorithm-engineer-facing workbench for diagnostics, comparison, and experimentation.

---

## Definition of done

A task is complete only when:

1. The requested behavior is implemented.
2. Relevant focused tests pass.
3. The full test suite passes, or unrelated failures are documented.
4. `git diff --check` passes.
5. The diff contains no unrelated changes.
6. Historical fixtures and expected values remain intact unless deliberately revised.
7. The agent reports verification commands and remaining limitations.
8. The human has reviewed the result.
