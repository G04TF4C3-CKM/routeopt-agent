# RouteOpt Agent Capstone Specification

## Track
Agents for Business.

## Problem
Dispatchers and operations analysts often need to reason about vehicle-routing scenarios, but raw optimization code is difficult to configure, run, and interpret. This project turns a legacy vehicle-routing optimization experiment into an agent-assisted decision workflow.

## Solution
RouteOpt Agent accepts a local scenario file containing pickup/dropoff loads, validates the input, runs a custom residual-graph routing optimizer, analyzes the before/after result, and produces a business-readable explanation.

## Core workflow

```text
LoadScenarioNode
  -> ValidateScenarioNode
  -> RunOptimizerNode
  -> AnalyzeSolutionNode
  -> ExplainSolutionNode
```

## Inputs
A local `.txt` file with one load per line:

```text
(pickup_x, pickup_y), (dropoff_x, dropoff_y)
```

## Outputs
- Initial driver count
- Final driver count
- Total route time before/after optimization
- Maximum driver time
- Feasibility under the configured time limit
- Final route assignments
- User-facing explanation

## Safety constraints
- Local files only; remote URLs are rejected.
- No API keys or credentials are required.
- No external side effects such as email, database writes, or cloud deployment are performed by the backend.
- The legacy optimizer is wrapped behind a stable interface so the UI/agent layer does not mutate internal graph state directly.

## Minimum success scenario
Given the sample 8-load scenario and a driver time limit of 12.0, the workflow reduces the route plan from 8 initial drivers to 3 final drivers while keeping the final maximum driver time below the limit.
