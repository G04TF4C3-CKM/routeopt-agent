# src/experimental_karp_mmc.py
"""Experimental extraction of the Karp / Mean‑Minimum‑Cycle (MMC) solver.

This module is **isolated** – it does **not** alter any production code path.
It provides the core functions that were originally defined in the legacy
notebook ``legacy_audit/KarpsMeanMinCycle_2.ipynb`` but stripped of all UI
printing, top‑level execution and Streamlit / matplotlib side‑effects.

The implementation is deliberately minimal: only the algorithmic skeleton is
kept.  Debug output is gated behind the ``wp`` (verbose) flag, which defaults
to ``False``.

If a future migration wants to expose the MMC solver, the production code
can import ``src.experimental_karp_mmc`` and call ``discharge_mmc``.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Dict, List, Tuple, Optional

import networkx as nx

# Use the same VRP utilities that the production code relies on, but keep the
# import local to this module so that the production path remains untouched.
from . import legacy_vrp as vr

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class MMCResult:
    """Result container for the MMC algorithm.

    Attributes
    ----------
    min_mean: Optional[float]
        The minimum mean weight of any discovered cycle (negative indicates a
        beneficial firing‑path). ``None`` if no cycle was found.
    cycle: Optional[List[int]]
        The list of vertex identifiers that form the cycle, ``None`` when no
        cycle exists.
    applied: bool
        ``True`` when the algorithm performed a discharge (i.e. a negative
        cycle was found and applied to the driver graph).
    message: str
        Optional human‑readable information.
    """

    min_mean: Optional[float]
    cycle: Optional[List[int]]
    applied: bool = False
    message: str = ""

# ---------------------------------------------------------------------------
# Helper functions – direct copies from the notebook, trimmed of noisy prints
# ---------------------------------------------------------------------------

def path_rebuild(v: int, pred: Dict[int, int]) -> List[int]:
    """Rebuild a path by following predecessor links.

    Parameters
    ----------
    v: int
        Starting vertex (typically the target of the path).
    pred: dict[int, int]
        Mapping ``vertex -> predecessor`` where ``-1`` denotes the artificial
        source.
    """
    path: List[int] = []
    visited = set()
    while v > -1:
        path.append(v)
        if v in visited:
            break
        visited.add(v)
        v = pred[v]
    return path


def cycle_rebuild(cycle_start: int, path: List[int]) -> List[int]:
    """Extract the minimal cycle containing ``cycle_start`` from ``path``.

    The algorithm walks backwards from ``cycle_start`` until the vertex repeats,
    then returns the slice that forms the directed cycle.
    """
    cycle: List[int] = []
    arr: List[int] = []
    visited = set()
    current_node = cycle_start
    i = len(path)
    while current_node not in visited and i >= 0:
        i -= 1
        visited.add(current_node)
        arr.append(current_node)
        if i - 1 >= 0:
            current_node = path[i - 1]
        else:
            break
    que = deque(arr)
    while que:
        q = que.popleft()
        if q == current_node:
            cycle = [q] + list(que) + [q]
            que = deque()
    cycle.reverse()
    return cycle


def big_cycle_rebuild(path: List[int], wp: bool = False) -> Tuple[List[int], Optional[int], Optional[int]]:
    """Return the *largest* contiguous cycle segment in ``path``.

    The function mirrors the notebook implementation but returns the cycle
    together with its left/right indices inside ``path``.  ``wp`` toggles the
    optional debug prints.
    """
    if wp:
        print(f"Enter: big_cycle_rebuild, path = {path}")
    cycle: List[int] = []
    arr: List[int] = []
    visited = set()
    i = len(path) - 1
    current_node = path[i]
    while current_node not in visited and i > 0:
        visited.add(current_node)
        arr.append(current_node)
        i -= 1
        current_node = path[i]
    cycle_start = current_node
    if wp:
        print(f"big_cycle_rebuild cycle_start = {cycle_start} (i = {i})")
    a = 0
    b = len(path) - 1
    left_index: Optional[int] = None
    right_index: Optional[int] = None
    while b > a:
        if path[a] == cycle_start and left_index is None:
            left_index = a
        else:
            if left_index is None:
                a += 1
        if path[b] == cycle_start and right_index is None:
            right_index = b
        else:
            if right_index is None:
                b -= 1
        if wp:
            print(f"(a, b) = {a,b}, left_index = {left_index}, right_index = {right_index}")
        if left_index is not None and right_index is not None:
            break
    if wp:
        print(f"Final indices: left_index = {left_index}, right_index = {right_index}")
    if left_index is not None and right_index is not None:
        cycle = path[left_index : right_index + 1]
    return cycle, left_index, right_index


def sort_edges(H: nx.DiGraph, wp: bool = False) -> Tuple[set, set, set, set, set, set]:
    """Classify edges of the residual graph into six buckets.

    The classification follows the original MMC paper and matches the notebook
    implementation.  Each set contains tuples ``(u, v, weight)``.
    """
    set_1 = set()
    set_2 = set()
    set_3 = set()
    set_4 = set()
    set_5 = set()
    set_6 = set()
    for u, v, w in H.edges(data="weight"):
        if u == -1 and v % 2 == 0:  # initial deletion
            set_1.add((u, v, w))
        elif v % 2 == 1 and u != 0 and v != -1:  # central addition
            set_2.add((u, v, w))
        elif u % 2 == 1 and v == 0:  # terminal deletion
            set_3.add((u, v, w))
        elif u == 0 and v % 2 == 1:  # initial addition
            set_4.add((u, v, w))
        elif u % 2 == 1 and u != -1 and v != -1:  # central deletion
            set_5.add((u, v, w))
        elif v == -1 and u % 2 == 0:  # terminal addition
            set_6.add((u, v, w))
        else:
            if wp:
                print(f"<<< ERROR >>> This edge {u, v, w} does not fit any bucket")
    return set_1, set_2, set_3, set_4, set_5, set_6


def add_to_que(que: List[set], e: Tuple[int, int, float], ebunch_idx: int) -> None:
    """Insert the reverse of edge ``e`` into the appropriate queue slot.

    ``que`` is the list ``[set_1, set_6, set_2, set_4, set_3, set_5]`` as built
    by the caller.  ``ebunch_idx`` indicates which set the original edge came
    from (0‑5).  The function mirrors the notebook logic.
    """
    (u, v, cost) = e
    if ebunch_idx == 0:
        que[1].add((v, u, -cost))
    elif ebunch_idx == 1:
        que[0].add((v, u, -cost))
    elif ebunch_idx == 2:
        que[5].add((v, u, -cost))
    elif ebunch_idx == 3:
        que[4].add((v, u, -cost))
    elif ebunch_idx == 4:
        que[3].add((v, u, -cost))
    elif ebunch_idx == 5:
        que[2].add((v, u, -cost))

# ---------------------------------------------------------------------------
# Core MMC algorithm – lightweight version.
# ---------------------------------------------------------------------------

def karp_mmc_mod(
    drivers_initial: vr.Drivers,
    que: List[set],
    wp: bool = False,
) -> Tuple[Optional[float], Optional[List[int]]]:
    """Run the MMC relaxation loop.

    Returns ``(min_mean, cycle)`` where ``cycle`` is a list of vertex IDs.  If no
    negative‑mean cycle is found, both values are ``None``.
    """
    H = drivers_initial.H
    n = len(H.nodes)
    d_1: Dict[int, Dict[int, float]] = {0: {v: float("inf") for v in H.nodes}}
    d_2: Dict[int, Dict[int, float]] = {0: {v: float("inf") for v in H.nodes}}
    source_1 = -1
    source_2 = 0
    d_1[0][source_1] = 0.0
    d_2[0][source_2] = 0.0
    pred: Dict[int, Optional[int]] = {v: None for v in H.nodes}
    drivers_dict_1: Dict[int, vr.Drivers] = {source_1: drivers_initial}
    drivers_dict_2: Dict[int, vr.Drivers] = {source_2: drivers_initial}
    paths_1: Dict[int, List[int]] = {source_1: [source_1]}
    paths_2: Dict[int, List[int]] = {source_2: [source_2]}
    updated = False
    relaxed = False
    k = 0
    current_depth_limit_1 = 0
    current_depth_limit_2 = 0
    while not relaxed and k < 6 * n + 6:
        k += 1
        d_1[k] = {}
        d_2[k] = {}
        if k / 3 > current_depth_limit_1 - 1:
            current_depth_limit_1 += 1
        if k / 3 > current_depth_limit_2 - 1:
            current_depth_limit_2 += 1
        ebunch_idx = (k - 1) % 6
        ebunch = deque(que[ebunch_idx])
        while ebunch:
            u, v, cost = ebunch.popleft()
            # Path‑1 side
            if u in paths_1 and len(paths_1[u]) > 0:
                prev_k_1 = len(paths_1[u]) - 1
                prev_cost_1 = d_1[prev_k_1][u]
            else:
                prev_k_1 = None
                prev_cost_1 = None
            # Path‑2 side
            if u in paths_2 and len(paths_2[u]) > 0:
                prev_k_2 = len(paths_2[u]) - 1
                prev_cost_2 = d_2[prev_k_2][u]
            else:
                prev_k_2 = None
                prev_cost_2 = None
            feasible_1 = None
            feasible_2 = None
            if prev_k_1 is not None:
                i = 0
                while d_1[prev_k_1 + 1 - i].get(v) is None:
                    i += 1
                d_1[prev_k_1 + 1][v] = d_1[prev_k_1 + 1 - i][v]
                if prev_cost_1 + cost < d_1[prev_k_1 + 1][v]:
                    pot_drivers_v_1, _ = vr.feasible_check(
                        u, v, paths_1[u], drivers_dict_1[u], wp=wp
                    )
                    feasible_1 = pot_drivers_v_1.hot_drivers == {}
            if prev_k_2 is not None:
                i = 0
                while d_2[prev_k_2 + 1 - i].get(v) is None:
                    i += 1
                d_2[prev_k_2 + 1][v] = d_2[prev_k_2 + 1 - i][v]
                if prev_cost_2 + cost < d_2[prev_k_2 + 1][v]:
                    pot_drivers_v_2, _ = vr.feasible_check(
                        u, v, paths_2[u], drivers_dict_2[u], wp=wp
                    )
                    feasible_2 = pot_drivers_v_2.hot_drivers == {}
            if feasible_1 or feasible_2:
                add_to_que(que, (u, v, cost), ebunch_idx)
                if feasible_1:
                    d_1[prev_k_1 + 1][v] = prev_cost_1 + cost
                    drivers_dict_1[v] = pot_drivers_v_1
                    paths_1[v] = paths_1[u] + [v]
                    updated = True
                if feasible_2:
                    d_2[prev_k_2 + 1][v] = prev_cost_2 + cost
                    drivers_dict_2[v] = pot_drivers_v_2
                    paths_2[v] = paths_2[u] + [v]
                    updated = True
        if k % 6 == 0:
            if paths_1.get(0):
                l = len(paths_1[0]) - 1
                return d_1[l][0] / l, paths_1[0]

            if updated:
                updated = False
            else:
                relaxed = True
    # Negative-cycle recovery through source_2 (vertex 0) is deferred to a
    # separate regression-driven task. Return (None, None) when no firing path was found.
    return None, None


def karp_mmc_mod_hire(
    drivers_initial: vr.Drivers,
    que: List[set],
    wp: bool = False,
) -> Tuple[Optional[float], Optional[List[int]]]:
    """Search for a feasible negative reconnection cycle through vertex 0.

    Unlike :func:`karp_mmc_mod`, this search retains every feasible path and
    its candidate-specific ``Drivers`` state.  The single-label searches are
    retained only because their successful relaxations drive the historical
    residual-edge requeue behavior.
    """
    H = drivers_initial.H
    n = len(H.nodes)
    source_1 = -1
    source_2 = 0

    d_1: Dict[int, Dict[int, float]] = {
        0: {v: float("inf") for v in H.nodes}
    }
    d_2: Dict[int, Dict[int, float]] = {
        0: {v: float("inf") for v in H.nodes}
    }
    d_1[0][source_1] = 0.0
    d_2[0][source_2] = 0.0

    d_3: Dict[int, List[Tuple[List[int], vr.Drivers, float]]] = {
        v: [] for v in H.nodes
    }
    d_3[source_2].append(([source_2], drivers_initial, 0.0))

    drivers_dict_1: Dict[int, vr.Drivers] = {source_1: drivers_initial}
    drivers_dict_2: Dict[int, vr.Drivers] = {source_2: drivers_initial}
    paths_1: Dict[int, List[int]] = {source_1: [source_1]}
    paths_2: Dict[int, List[int]] = {source_2: [source_2]}

    updated = False
    relaxed = False
    k = 0
    while not relaxed and k < 3 * n:
        k += 1
        d_1[k] = {}
        d_2[k] = {}
        ebunch_idx = (k - 1) % 6
        ebunch = deque(que[ebunch_idx])

        while ebunch:
            u, v, cost = ebunch.popleft()

            if u in paths_1 and paths_1[u]:
                prev_k_1 = len(paths_1[u]) - 1
                prev_cost_1 = d_1[prev_k_1][u]
            else:
                prev_k_1 = None
                prev_cost_1 = None

            if u in paths_2 and paths_2[u]:
                prev_k_2 = len(paths_2[u]) - 1
                prev_cost_2 = d_2[prev_k_2][u]
            else:
                prev_k_2 = None
                prev_cost_2 = None

            feasible_1 = None
            feasible_2 = None
            feasible_3 = None

            for allpath, prev_drivers, prev_cost_3 in d_3[u]:
                if len(allpath) == 1:
                    pot_drivers_v_3, _ = vr.feasible_check(
                        u, v, allpath, prev_drivers, wp=wp
                    )
                elif len(allpath) > k // 3 - 1:
                    if v == allpath[-2]:
                        continue
                    pot_drivers_v_3, _ = vr.feasible_check(
                        u, v, allpath, prev_drivers, wp=wp
                    )
                else:
                    continue

                if pot_drivers_v_3.hot_drivers == {}:
                    candidate_cost = prev_cost_3 + cost
                    candidate_path = allpath + [v]
                    d_3[v].append(
                        (candidate_path, pot_drivers_v_3, candidate_cost)
                    )
                    feasible_3 = True
                    if len(allpath) != 1 and v == source_2 and candidate_cost < 0:
                        return candidate_cost / len(allpath), candidate_path

            if prev_k_1 is not None:
                i = 0
                while d_1[prev_k_1 + 1 - i].get(v) is None:
                    i += 1
                d_1[prev_k_1 + 1][v] = d_1[prev_k_1 + 1 - i][v]
                if prev_cost_1 + cost < d_1[prev_k_1 + 1][v]:
                    pot_drivers_v_1, _ = vr.feasible_check(
                        u, v, paths_1[u], drivers_dict_1[u], wp=wp
                    )
                    feasible_1 = pot_drivers_v_1.hot_drivers == {}

            if prev_k_2 is not None:
                i = 0
                while d_2[prev_k_2 + 1 - i].get(v) is None:
                    i += 1
                d_2[prev_k_2 + 1][v] = d_2[prev_k_2 + 1 - i][v]
                if prev_cost_2 + cost < d_2[prev_k_2 + 1][v]:
                    pot_drivers_v_2, _ = vr.feasible_check(
                        u, v, paths_2[u], drivers_dict_2[u], wp=wp
                    )
                    feasible_2 = pot_drivers_v_2.hot_drivers == {}

            if feasible_1 or feasible_2:
                add_to_que(que, (u, v, cost), ebunch_idx)
                if feasible_1:
                    d_1[prev_k_1 + 1][v] = prev_cost_1 + cost
                    drivers_dict_1[v] = pot_drivers_v_1
                    paths_1[v] = paths_1[u] + [v]
                    updated = True
                if feasible_2:
                    d_2[prev_k_2 + 1][v] = prev_cost_2 + cost
                    drivers_dict_2[v] = pot_drivers_v_2
                    paths_2[v] = paths_2[u] + [v]
                    updated = True
            elif feasible_3:
                updated = True

        if k % 6 == 0:
            if updated:
                updated = False
            else:
                relaxed = True

    return None, None


def _apply_source_rooted_cycle(drivers: vr.Drivers, cycle: List[int]) -> None:
    """Apply a closed source-rooted version-2 residual cycle.

    This includes both source-side shift cycles and cross-boundary cycles.
    """
    if len(cycle) < 3 or cycle[0] != 0 or cycle[-1] != 0:
        raise ValueError("Version-2 augmentation must be a cycle starting and ending at 0")

    ebunch_del, ebunch_add, aug_list = vr.aug_path(cycle, drivers.H)
    if not aug_list:
        raise ValueError("Version-2 augmentation produced an empty augmentation list")
    if len(ebunch_add) != len(ebunch_del):
        raise ValueError(
            "Version-2 source-rooted cycle requires equal addition and deletion queues"
        )
    if len(aug_list) != len(ebunch_add) + len(ebunch_del):
        raise ValueError(
            "Version-2 augmentation trace is incompatible with its mutation queues"
        )

    missing_deletions = [
        (u, v) for u, v in ebunch_del if not drivers.G.has_edge(u, v)
    ]
    if missing_deletions:
        raise ValueError(
            f"Version-2 augmentation references missing deletion edges: {missing_deletions}"
        )

    additions = deque(ebunch_add)
    deletions = deque(ebunch_del)
    first_operation_is_add = aug_list[0][1] % 2 == 1
    mutation_count = len(aug_list)
    for mutation_position in range(1, mutation_count + 1):
        operation_is_add = (
            mutation_position % 2 == 1
        ) == first_operation_is_add
        if operation_is_add:
            u, v, time, weight = additions.popleft()
            drivers.G.add_edge(u, v, time=time, weight=weight)
        else:
            u, v = deletions.popleft()
            drivers.G.remove_edge(u, v)

    drivers.update()


def discharge_mmc(
    drivers: vr.Drivers,
    wp: bool = False,
    version: Optional[int] = None,
) -> Optional[List[int]]:
    """Experimental discharge using the MMC algorithm.

    Returns the applied cycle if a negative‑mean cycle is found and fired, or
    ``None`` otherwise.
    """
    if version is not None and version not in (1, 2):
        raise NotImplementedError(
            f"Experimental MMC version {version} is not implemented"
        )
    set_1, set_2, set_3, set_4, set_5, set_6 = sort_edges(drivers.H, wp=wp)
    que = [set_1, set_6, set_2, set_4, set_3, set_5]
    if version == 2:
        min_mean, cycle = karp_mmc_mod_hire(drivers, que, wp=wp)
    else:
        min_mean, cycle = karp_mmc_mod(drivers, que, wp=wp)
    if cycle is None:
        if wp:
            print("No MMC cycle found – discharge aborted.")
        return None
    if min_mean is not None and min_mean < 0:
        if version == 2:
            _apply_source_rooted_cycle(drivers, cycle)
            return cycle
        augment = vr.aug_path(cycle, drivers.H)
        ebunch_del, ebunch_add, _ = augment
        for edge in ebunch_del:
            u, v = edge[:2]
            if drivers.G.has_edge(u, v):
                drivers.G.remove_edge(u, v)
        for edge in ebunch_add:
            u, v, t, c = edge
            drivers.G.add_edge(u, v, time=t, weight=c)
        drivers.update()
        return cycle
    return None

# End of experimental_karp_mmc.py
