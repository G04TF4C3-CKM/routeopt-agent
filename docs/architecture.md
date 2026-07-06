# Architecture

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
