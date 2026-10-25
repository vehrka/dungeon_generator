"""Tests for the combined grammar and the DCombined generator

Run with: python -m pytest tests
"""

import pytest

from dungeon_fx11 import DCombined
from grammar.combined import GRAMMAR, PRESETS, simulate, spectral_radius

SEEDS = range(1, 301)


@pytest.mark.parametrize("preset", PRESETS)
def test_ranges_cover_d20(preset):
    for symbol, rule in GRAMMAR.items():
        covered = sorted(
            roll
            for var in rule["variants"]
            if var["ranges"].get(preset)
            for roll in range(var["ranges"][preset][0], var["ranges"][preset][1] + 1)
        )
        assert covered == list(range(1, 21)), f"{symbol} {preset}"


@pytest.mark.parametrize("preset", PRESETS)
def test_grammar_is_subcritical(preset):
    assert spectral_radius(preset) < 1


@pytest.mark.parametrize("preset", PRESETS)
def test_simulation_terminates(preset):
    for seed in SEEDS:
        _, expansions = simulate(preset, seed)
        assert expansions < 10000


def can_enter(vertex, collected):
    """A gate can be entered when its objects were collected. OFF gates start open"""
    if vertex["type"] not in ("lock", "gate") or vertex["name"].endswith(" OFF"):
        return True
    return all(obj.uid in collected for obj in vertex["objects"])


def reachable(graph):
    """Vertices reachable from START collecting every object found on the way"""
    neighbours = {v.index: set() for v in graph.vs}
    for edge in graph.es:
        neighbours[edge.source].add(edge.target)
        if not edge["oneway"]:
            neighbours[edge.target].add(edge.source)
    start = graph.vs.find(name="START").index
    collected = set()
    reached = {start}
    changed = True
    while changed:
        changed = False
        stack = list(reached)
        while stack:
            vertex = graph.vs[stack.pop()]
            if vertex["type"] not in ("lock", "gate") and vertex["objects"]:
                collected.update(obj.uid for obj in vertex["objects"])
            for nxt in neighbours[vertex.index]:
                if nxt not in reached and can_enter(graph.vs[nxt], collected):
                    reached.add(nxt)
                    stack.append(nxt)
                    changed = True
    return reached


@pytest.mark.parametrize("reduce", [True, False])
@pytest.mark.parametrize("preset", PRESETS)
def test_dungeons_are_solvable(preset, reduce):
    for seed in SEEDS:
        graph = DCombined(
            seed=seed, size=preset, reduce=reduce, maxnodes=10000, maxiter=10000
        ).get_graph()
        assert not graph.vs.select(color_eq="#d55e00"), f"unexpanded vertices, seed {seed}"
        reached = reachable(graph)
        goal = graph.vs.find(name="GOAL").index
        assert goal in reached, f"GOAL unreachable, preset {preset} seed {seed}"
        pickups = [
            v.index for v in graph.vs if v["type"] in ("key", "bosskey", "item", "switch", "lever")
        ]
        assert set(pickups) <= reached, f"unreachable pickup, preset {preset} seed {seed}"
