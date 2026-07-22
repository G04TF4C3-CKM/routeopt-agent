# tests/test_experimental_karp_mmc.py
"""Tests for the experimental Karp/MMC extraction module.
These tests verify that the module can be imported and that a few core
utilities behave as expected on tiny synthetic data.
"""

from pathlib import Path

import networkx as nx

from src import legacy_vrp as vr
from src.experimental_karp_mmc import (
    path_rebuild,
    cycle_rebuild,
    sort_edges,
    MMCResult,
    discharge_mmc,
)


def test_path_and_cycle_rebuild():
    # Simple predecessor map forming a line 0 -> 1 -> 2 -> -1 (source)
    pred = {2: 1, 1: 0, 0: -1, -1: -1}
    path = path_rebuild(2, pred)
    assert path == [2, 1, 0]
    # Rebuild minimal cycle: use a fabricated path that repeats a node
    path2 = [0, 1, 2, 1, 0]
    cycle = cycle_rebuild(1, path2)
    assert cycle == [1, 1]


def test_sort_edges_and_discharge():
    # Build a tiny residual graph matching the categories used by sort_edges
    H = nx.DiGraph()
    H.add_edge(-1, 2, weight=1.0)   # set_1: u=-1, v even
    H.add_edge(2, 3, weight=2.0)    # set_2: v odd, u != 0
    H.add_edge(1, 0, weight=-2.0)   # set_3: u odd, v=0
    H.add_edge(0, 1, weight=2.0)    # set_4: u=0, v odd
    H.add_edge(1, 2, weight=-0.5)   # set_5: u odd, v not -1
    H.add_edge(2, -1, weight=-1.0)  # set_6: v=-1, u even
    sets = sort_edges(H)
    for s in sets:
        assert len(s) == 1
    # Do not call discharge_mmc on this synthetic graph: the full MMC
    # discharge path expects a populated legacy Drivers object with G/H state.


def test_mmc_result_container():
    result = MMCResult(min_mean=None, cycle=None, applied=False, message="no cycle")

    assert result.min_mean is None
    assert result.cycle is None
    assert result.applied is False


def test_discharge_mmc_rejects_unsupported_version_before_touching_driver_state():
    class DummyDrivers:
        pass

    import pytest

    with pytest.raises(NotImplementedError):
        discharge_mmc(DummyDrivers(), version=999)


def test_karp_first_firing_path_reduces_drivers():
    fixture_path = Path(__file__).parent / "fixtures" / "loads_5_8_hiring_firing_path.txt"
    graph = vr.create_graph_from_file(str(fixture_path))
    drivers = vr.Drivers(graph, time_limit=8.0, res_type="mod", wp=False)

    assert len(drivers.labels) == 5

    applied = discharge_mmc(drivers, wp=False, version=1)

    assert applied is not None
    assert applied[0] == -1
    assert applied[-1] == 0
    assert len(drivers.labels) == 4
    assert drivers.hot_drivers == {}
    assert drivers.max_time <= 8.0


def test_karp_reconnection_cycle_reduces_time_at_two_drivers():
    import pytest

    fixture_path = Path(__file__).parent / "fixtures" / "loads_5_8_hiring_firing_path.txt"
    graph = vr.create_graph_from_file(str(fixture_path))
    drivers = vr.Drivers(graph, time_limit=12.0, res_type="mod", wp=False)

    firing_paths = [
        [-1, 10, 1, 0],
        [-1, 2, 7, 0],
        [-1, 4, 5, 0],
    ]
    for path in firing_paths:
        deletion_edges, addition_edges, _ = vr.aug_path(path, drivers.H)
        drivers.G.remove_edges_from(deletion_edges)
        for u, v, time, weight in addition_edges:
            drivers.G.add_edge(u, v, time=time, weight=weight)
        drivers.update()

    assert len(drivers.labels) == 2
    assert drivers.hot_drivers == {}
    assert drivers.max_time <= 12.0
    assert sum(drivers.time.values()) == pytest.approx(
        21.78032107205433,
        abs=1e-6,
    )

    cycle = discharge_mmc(drivers, wp=False, version=2)

    assert cycle is not None
    assert cycle[0] == 0
    assert cycle[-1] == 0
    assert -1 in cycle[1:-1]
    assert len(drivers.labels) == 2
    assert drivers.hot_drivers == {}
    assert drivers.max_time <= 12.0
    assert sum(drivers.time.values()) == pytest.approx(
        21.677714866639274,
        abs=1e-6,
    )
