from src.routing_engine import solve_routing_problem


def test_sample_8_loads_solves_feasibly():
    result = solve_routing_problem("data/sample_8_loads.txt", time_limit=12.0)
    assert result["load_count"] == 8
    assert result["initial_driver_count"] == 8
    assert result["final_driver_count"] == 3
    assert result["feasible"] is True
    assert result["max_driver_time"] <= 12.0
