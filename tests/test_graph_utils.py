"""Tests for the solvability check of utils/graph_utils.py

Run with: python -m pytest tests
"""

import logging
from types import SimpleNamespace
from typing import Any

import igraph
import pytest

from dungeon_fx11 import DCombined
from utils.graph_utils import progress, reachable, steps, unsolvable_reasons

KEY = SimpleNamespace(uid="spam", name="spam key 1")


def graph(
    vertices: list[tuple[Any, ...]],
    edges: list[tuple[int, int]],
    oneway: list[bool] | None = None,
) -> igraph.Graph:
    """Graph from (type, name, objects) vertices and (source, target) edges"""
    g = igraph.Graph(directed=True)
    g.add_vertices(len(vertices))
    g.vs["type"], g.vs["name"], g.vs["objects"] = (list(attr) for attr in zip(*vertices))
    g.add_edges(edges)
    if oneway is not None:
        g.es["oneway"] = oneway
    return g


START = ("st", "START", None)
GOAL = ("gl", "GOAL", None)
LOCK = ("lock", "Use spam key 1", [KEY])
PICKUP = ("key", "Get spam key 1", [KEY])


def test_key_before_lock_is_solvable() -> None:
    g = graph([START, GOAL, LOCK, PICKUP], [(0, 3), (0, 2), (2, 1)])

    assert reachable(g) == {0, 1, 2, 3}
    assert unsolvable_reasons(g) == []


def test_key_behind_its_lock_is_reported() -> None:
    g = graph([START, GOAL, LOCK, PICKUP], [(0, 2), (2, 1), (2, 3)])

    assert reachable(g) == {0}
    assert unsolvable_reasons(g) == [
        "GOAL unreachable",
        "Use spam key 1 needs spam key 1",
    ]


def test_missing_key_is_reported() -> None:
    g = graph([START, GOAL, LOCK], [(0, 2), (2, 1)])

    assert unsolvable_reasons(g) == [
        "GOAL unreachable",
        "Use spam key 1 needs spam key 1",
    ]


def test_one_way_edge_cannot_be_walked_back() -> None:
    eggs = ("n", "n", None)
    g = graph([START, GOAL, eggs], [(0, 1), (2, 0)], oneway=[False, True])

    assert reachable(g) == {0, 1}
    assert unsolvable_reasons(g) == []


def test_off_gate_starts_open() -> None:
    off = ("gate", "Check lever 1 OFF", [KEY])
    g = graph([START, GOAL, off], [(0, 2), (2, 1)])

    assert unsolvable_reasons(g) == []


def test_limits_hit_logs_the_blocking_lock(caplog: pytest.LogCaptureFixture) -> None:
    for seed in range(1, 51):
        with caplog.at_level(logging.WARNING, logger="utils.graph_utils"):
            caplog.clear()
            graph_ = DCombined(seed=seed, size="L", maxnodes=20, maxiter=10).get_graph()
        reasons = unsolvable_reasons(graph_)
        unsolvable = [r.message for r in caplog.records if "unsolvable" in r.message]
        if reasons:
            assert unsolvable == [f"Dungeon unsolvable: {'; '.join(reasons)}"], f"seed {seed}"
        else:
            assert unsolvable == [], f"seed {seed}"


def reduced(g: igraph.Graph) -> igraph.Graph:
    """Graph after the merge step of the generator"""
    dungeon = DCombined(seed=1)
    dungeon._g = g
    dungeon._reduce_graph()
    return dungeon.get_graph()


def test_rooms_of_the_same_type_merge_keeping_their_exits() -> None:
    spam = ("t", "t", None)
    eggs = ("c", "c", None)
    g = graph(
        [START, GOAL, spam, spam, eggs, eggs, ("n", "n", None)],
        [(0, 2), (2, 3), (3, 4), (4, 5), (5, 1), (3, 6)],
        oneway=[False] * 6,
    )

    g = reduced(g)

    assert g.vs["type"] == ["st", "gl", "t", "c", "n"]
    assert sorted(g.get_edgelist()) == [(0, 2), (2, 3), (2, 4), (3, 1)]


def test_rooms_joined_one_way_do_not_merge() -> None:
    spam = ("e", "e", None)
    g = graph([START, GOAL, spam, spam], [(0, 2), (2, 3), (3, 1)], oneway=[False, True, False])

    g = reduced(g)

    assert g.vcount() == 4
    assert g.es["oneway"] == [False, True, False]


def test_merge_keeps_one_way_exits() -> None:
    spam = ("p", "p", None)
    eggs = ("e", "e", None)
    g = graph(
        [START, GOAL, spam, spam, eggs],
        [(0, 2), (2, 3), (3, 4), (4, 2), (3, 1)],
        oneway=[False, False, True, True, False],
    )

    g = reduced(g)

    oneway = {edge.tuple: edge["oneway"] for edge in g.es}
    assert oneway == {(0, 2): False, (2, 3): True, (3, 2): True, (2, 1): False}


def test_steps_count_a_gate_as_one_step() -> None:
    g = graph([START, GOAL, LOCK, ("n", "n", None)], [(0, 3), (3, 2), (2, 1)])

    assert steps(g, 0, [3, 1]) == [1, 2]


def test_progress_runs_from_start_to_the_boss() -> None:
    spam = ("e", "e", None)
    g = graph(
        [START, GOAL, spam, spam, spam, ("eb", "eb", None)],
        [(0, 2), (2, 3), (3, 4), (4, 5), (5, 1)],
    )

    assert [progress(g, vi) for vi in (0, 2, 4, 5)] == [0, 0.25, 0.75, 1]


def test_remove_room_rewires_a_two_way_neighbour() -> None:
    spam = ("R", "R", None)
    eggs = ("n", "n", None)
    g = graph([START, GOAL, spam, eggs], [(0, 2), (2, 0), (2, 1)])
    dungeon = DCombined(seed=1)
    dungeon._g = g

    dungeon._remove_room(g.vs[2], 3)

    assert g.vs["type"] == ["st", "gl", "n"]
    assert sorted(g.get_edgelist()) == [(0, 2), (2, 0), (2, 1)]
