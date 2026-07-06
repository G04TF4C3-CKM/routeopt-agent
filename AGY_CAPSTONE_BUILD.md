# RouteOpt Agent — Capstone Build Instructions for agy

## Project context

This repository is `routeopt-agent`, a capstone project for Kaggle's 5-Day AI Agents: Intensive Vibe Coding Course with Google.

The project wraps an existing custom vehicle-routing optimization backend in an agent-style application. The backend already works and has tests.

Current verified backend behavior:

    python app.py data/sample_8_loads.txt --time-limit 12
    python -m pytest -q

Expected result:

- The sample 8-load problem reduces from 8 drivers to 3 drivers.
- The final maximum driver time is below the 12.0 time limit.
- The test suite passes.

## Primary goal

Build a capstone-ready application layer around the existing backend.

The app should demonstrate:

1. A practical business use case: vehicle-routing and driver-plan analysis.
2. An agent-style workflow: load scenario, validate scenario, optimize, analyze, explain.
3. Safety-conscious development: local-only execution, input validation, no secrets, no destructive actions.
4. Clear documentation and demo-readiness.

## Critical constraint

Do **not** rewrite the optimization algorithm.

Treat these files as legacy solver internals unless a test failure requires a narrow, justified patch:

- `src/legacy_vrp.py`
- core behavior in `src/routing_engine.py`

If edits are necessary, keep them minimal and preserve existing outputs for:

    python app.py data/sample_8_loads.txt --time-limit 12
    python -m pytest -q

The optimization engine is the user's original work. The task is to wrap, document, validate, visualize, and present it — not replace it.

## Existing project structure

    routeopt-agent/
      README.md
      requirements.txt
      app.py
      src/
        legacy_vrp.py
        routing_engine.py
        scenario_loader.py
        result_analyzer.py
        safety.py
        agent_workflow.py
      data/
        sample_8_loads.txt
        sample_10_informative.txt
        sample_10_deep_relaxation.txt
        sample_5_hiring_firing.txt
      specs/
        capstone_spec.md
        scenarios.md
      docs/
        architecture.md
      tests/

## Requested build

Add a simple Streamlit app that lets a user run the routing workflow interactively.

Create:

    streamlit_app.py

The app should allow the user to:

1. Select one of the sample data files from `data/`.
2. Set a driver time limit, default `12.0`.
3. Run the routing workflow.
4. View:
   - initial driver count
   - final driver count
   - driver reduction
   - initial total route time
   - final total route time
   - route-time savings
   - max driver time
   - feasibility status
   - final routes
   - generated explanation text
5. Show a simple route visualization if feasible.

The visualization can be modest. A matplotlib chart or simple plotted pickup/dropoff points is enough. Do not overbuild.

## Preserve CLI behavior

The existing CLI must continue to work:

    python app.py data/sample_8_loads.txt --time-limit 12

Do not remove or break this entry point.

## Tests

Add or update tests for any new non-UI logic.

Do not attempt to unit-test Streamlit directly unless it is simple. Instead, keep business logic in importable functions and test those.

The following must pass:

    python -m pytest -q

## Documentation updates

Update `README.md` so it is capstone-ready.

The README should include:

1. Project title: RouteOpt Agent
2. Short subtitle: Agent-assisted vehicle-routing optimization and explanation
3. Problem statement
4. Solution overview
5. Architecture
6. Course concepts demonstrated:
   - Agent / workflow graph
   - Antigravity / agy CLI usage
   - Security features / input validation
   - Deployability via local Streamlit app
   - Spec-driven development
7. Setup instructions
8. CLI usage
9. Streamlit usage
10. Demo script
11. Safety notes
12. No API keys or credentials required

Add a short note that the project runs locally and does not require a login, external service, or production credentials.

## Architecture documentation

Update or add documentation under `docs/`.

At minimum, create or update:

    docs/architecture.md

It should describe this workflow:

    User
      -> Streamlit UI or CLI
      -> LoadScenarioNode
      -> ValidateScenarioNode
      -> RunOptimizerNode
      -> AnalyzeSolutionNode
      -> ExplainSolutionNode
      -> Results

Mention that invalid inputs stop before optimization.

## Capstone writeup support

Create:

    docs/kaggle_writeup_draft.md
    docs/video_script.md

The writeup draft should be under 2,500 words and include:

- title
- subtitle
- track recommendation: Agents for Business
- problem
- solution
- architecture
- agent workflow
- implementation details
- safety
- what was built with agy / Antigravity CLI
- future work

The video script should be 5 minutes or less and include:

1. Problem statement
2. Why agents
3. Architecture diagram walkthrough
4. Live demo using Streamlit
5. Backend/test proof
6. Closing value statement

## Safety requirements

Do not add code that sends emails, calls external APIs, uploads files externally, or requires credentials.

Do not include API keys, passwords, tokens, or private machine paths in committed files.

Validate uploaded or selected input files before solving.

If adding file upload support in Streamlit, restrict expected format to the existing load format:

    (pickup_x, pickup_y), (dropoff_x, dropoff_y)

Reject malformed lines gracefully with a user-facing error.

## Development style

Use clear, boring, maintainable Python.

Prefer small functions.

Do not introduce unnecessary frameworks.

Do not add heavy dependencies unless needed.

Keep the project runnable with:

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    streamlit run streamlit_app.py

If Streamlit is added, update `requirements.txt`.

## Acceptance criteria

The build is complete when all of these pass:

    python app.py data/sample_8_loads.txt --time-limit 12
    python -m pytest -q
    streamlit run streamlit_app.py

The Streamlit app should run locally and show a complete result for `data/sample_8_loads.txt`.

The README should explain enough for a Kaggle judge or GitHub reader to run the project.

Before finishing, provide a concise summary of:

- files changed
- tests run
- any risks or known limitations
- any recommended next steps