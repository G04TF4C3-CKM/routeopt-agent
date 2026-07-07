# Architecture

The system consists of two interaction surfaces:

* **CLI / UI** – Users can run the original CLI (`app.py`) or the new Streamlit front‑end (`streamlit_app.py`). Both invoke the same deterministic workflow.
* **RouteOpt Agent Workflow** – The core workflow nodes (load, validate, run optimizer, analyze, explain) remain unchanged.

```text
User / UI / CLI
    |
    v
RouteOpt Agent Workflow
    |
    +--> LoadScenarioNode
    +--> ValidateScenarioNode
    +--> RunOptimizerNode
    +--> AnalyzeSolutionNode
    +--> ExplainSolutionNode
    |
    v
Stable routing_engine.solve_routing_problem()
    |
    v
legacy_vrp.py custom residual-graph VRP optimizer
```

The Streamlit layer simply collects user parameters, calls `run_routing_workflow`, and presents the resulting metrics and a minimal Matplotlib visualization.


```text
User / UI / CLI
    |
    v
RouteOpt Agent Workflow
    |
    +--> LoadScenarioNode
    +--> ValidateScenarioNode
    +--> RunOptimizerNode
    +--> AnalyzeSolutionNode
    +--> ExplainSolutionNode
    |
    v
Stable routing_engine.solve_routing_problem()
    |
    v
legacy_vrp.py custom residual-graph VRP optimizer
```

The app uses a deterministic workflow first. A later LLM layer can call this backend to narrate results, ask clarifying questions, or prepare reports, but the core solver remains testable and reproducible.

### Solver mode

The current production solver mode is `bellman_discharge`. It repeatedly calls the legacy Bellman-Ford discharge routine through `routing_engine.solve_routing_problem()`.

The solver API now includes a forward-compatible `solver_mode` argument and an optional `progress_callback` hook. These are intended to support future UI progress reporting and later experimental solver modes such as Karp/MMC residual search, while preserving the current default behavior.

