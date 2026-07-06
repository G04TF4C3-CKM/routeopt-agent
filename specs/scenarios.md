# Behavior Scenarios

```gherkin
Feature: Agent-assisted vehicle-routing optimization

Scenario: Valid routing scenario is optimized
  Given a local scenario file with 8 pickup/dropoff loads
  And the driver time limit is 12.0
  When the RouteOpt Agent workflow runs
  Then the scenario is validated
  And the optimizer produces a feasible route plan
  And the final driver count is lower than the initial driver count
  And the workflow returns a plain-language explanation

Scenario: Missing scenario file is rejected
  Given a scenario path that does not exist
  When the RouteOpt Agent workflow runs
  Then the workflow returns an error
  And the optimizer is not executed

Scenario: Remote URLs are rejected
  Given a scenario path beginning with http:// or https://
  When the RouteOpt Agent workflow runs
  Then the workflow rejects the input as non-local
  And no external request is made
```
