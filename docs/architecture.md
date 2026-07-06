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
