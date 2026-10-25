"""Tests for the solvability check of utils/graph_utils.py

Run with: python -m pytest tests
"""

import logging
from types import SimpleNamespace

import igraph

from dungeon_fx11 import DCombined
from utils.graph_utils import reachable, unsolvable_reasons

KEY = SimpleNamespace(uid="spam", name="spam key 1")


def graph(vertices, edges, oneway=None):
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


def test_key_before_lock_is_solvable():
    g = graph([START, GOAL, LOCK, PICKUP], [(0, 3), (0, 2), (2, 1)])

    assert reachable(g) == {0, 1, 2, 3}
    assert unsolvable_reasons(g) == []


def test_key_behind_its_lock_is_reported():
    g = graph([START, GOAL, LOCK, PICKUP], [(0, 2), (2, 1), (2, 3)])

    assert reachable(g) == {0}
    assert unsolvable_reasons(g) == [
        "GOAL unreachable",
        "Use spam key 1 needs spam key 1",
    ]


def test_missing_key_is_reported():
    g = graph([START, GOAL, LOCK], [(0, 2), (2, 1)])

    assert unsolvable_reasons(g) == [
        "GOAL unreachable",
        "Use spam key 1 needs spam key 1",
    ]


def test_one_way_edge_cannot_be_walked_back():
    eggs = ("n", "n", None)
    g = graph([START, GOAL, eggs], [(0, 1), (2, 0)], oneway=[False, True])

    assert reachable(g) == {0, 1}
    assert unsolvable_reasons(g) == []


def test_off_gate_starts_open():
    off = ("gate", "Check lever 1 OFF", [KEY])
    g = graph([START, GOAL, off], [(0, 2), (2, 1)])

    assert unsolvable_reasons(g) == []


def test_limits_hit_logs_the_blocking_lock(caplog):
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
