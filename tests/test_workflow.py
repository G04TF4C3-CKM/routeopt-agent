from src.agent_workflow import run_routing_workflow


def test_workflow_returns_explanation():
    state = run_routing_workflow("data/sample_8_loads.txt", time_limit=12.0)
    assert state.errors == []
    assert state.valid is True
    assert state.result is not None
    assert state.analysis["drivers_saved"] == 5
    assert "reduced the plan" in state.explanation
